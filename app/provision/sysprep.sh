#!/bin/bash
# Sysprep images to prepare for upload to virt server

function worker {
echo "[+] Creating Worker"
cp ubuntu_qemu/qemu-ubuntu14-base.qcow2 ubuntu_qemu/ubuntu14-worker.qcow2
echo "[+] Sysprepping"
virt-sysprep -a ubuntu_qemu/ubuntu14-worker.qcow2

virt-copy-in -a ubuntu_qemu/ubuntu14-worker.qcow2 configure.sh /

virt-sysprep --enable customize \
    --root-password password:s3cur3password \
    --firstboot ./configure.sh \
    --hostname $HOST-worker \
    -a ubuntu_qemu/ubuntu14-worker.qcow2
}

function DB {
echo "[+] Creating DB"
echo "[+] Sysprepping"

cp ubuntu_qemu/qemu-ubuntu14-base.qcow2 ubuntu_qemu/ubuntu14-DB.qcow2

virt-sysprep -a ubuntu_qemu/ubuntu14-DB.qcow2

virt-copy-in -a ubuntu_qemu/ubuntu14-DB.qcow2 configure.sh /

virt-sysprep --enable customize \
    --root-password password:s3cur3password \
    --firstboot ./configure.sh \
    --hostname $HOST-DB \
    -a ubuntu_qemu/ubuntu14-DB.qcow2
}

function control {
echo "[+] Creating Control"
echo "[+] Sysprepping"

cp ubuntu_qemu/qemu-ubuntu14-base.qcow2 ubuntu_qemu/ubuntu14-control.qcow2

virt-sysprep -a ubuntu_qemu/ubuntu14-control.qcow2

virt-copy-in -a ubuntu_qemu/ubuntu14-control.qcow2 configure.sh /

virt-sysprep --enable customize \
    --root-password password:s3cur3password \
    --firstboot ./configure.sh \
    --hostname $HOST-control \
    -a ubuntu_qemu/ubuntu14-control.qcow2
}

usage()
{
cat << EOF
usage: $0 options

Sysprep images to prepare for upload to virt server

OPTIONS:
   -h      Show this message
   -c      client name
   -r      role [worker|DB|control|all]
ex. sysprep.sh -c newclient -r all
EOF
}

HOST=
ROLE=
while getopts “hc:r:” OPTION
do
     case $OPTION in
         h)
             usage
             exit 1
             ;;
         c)
             HOST=$OPTARG
             ;;
         r)
             ROLE=$OPTARG
             ;;
         ?)
             usage
             exit
             ;;
     esac
done

if [[ -z $HOST ]] || [[ -z $ROLE ]]
then
     usage
     exit 1
fi


if [[ "$ROLE" =~ "worker" ]]; then
    echo "[!] Running worker!"
    worker
elif [[ "$ROLE" =~ "DB" ]]; then
    echo "[!] Running DB!"
    DB
elif [[ "$ROLE" =~ "control" ]]; then
    echo "[!] Running control!"
    control
elif [[ "$ROLE" =~ "all" ]]; then
    echo "[!] Running all!"
    echo $PWD
    DB
    control
    worker
else
    usage
    exit 1
fi
