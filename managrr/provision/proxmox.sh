#!/bin/bash
#http://www.plainlystated.com/2014/03/creating-a-vm-kvm-proxmox/
#Uploads images to storage and provisions machine






function worker {
DRIVE=ubuntu14-worker
HOSTNAME=$(ssh root@$NODE bash -c "'
cat /etc/hostname'")

ssh root@$NODE bash -c "'
pvesh create /nodes/$HOSTNAME/qemu -vmid $VID -name $CLIENT-worker -memory 2048 -sockets 1 -cores 4 -net0 e1000,bridge=$INTERFACE -net1 e1000,bridge=vmbr1 -virtio0=virt:$VID/ubuntu14-worker.qcow2'"

mkdir /mnt/virt/images/$VID
mv ubuntu_qemu/$DRIVE.qcow2 /mnt/virt/images/$VID/

ssh root@$NODE bash -c "'pvesh create /nodes/$HOSTNAME/qemu/$VID/status/start'"
}

function DB {
DRIVE=ubuntu14-DB
HOSTNAME=$(ssh root@$NODE bash -c "'
cat /etc/hostname'")

ssh root@$NODE bash -c "'
pvesh create /nodes/$HOSTNAME/qemu -vmid $VID -name $CLIENT-DB -memory 2048 -sockets 2 -cores 4 -net0 e1000,bridge=$INTERFACE -net1 e1000,bridge=vmbr1 -virtio0=virt:$VID/ubuntu14-DB.qcow2'"

mkdir /mnt/virt/images/$VID
mv ubuntu_qemu/$DRIVE.qcow2 /mnt/virt/images/$VID/

ssh root@$NODE bash -c "'pvesh create /nodes/$HOSTNAME/qemu/$VID/status/start'"
}

function control {
DRIVE=ubuntu14-control
HOSTNAME=$(ssh root@$NODE bash -c "'
cat /etc/hostname'")

ssh root@$NODE bash -c "'
pvesh create /nodes/$HOSTNAME/qemu -vmid $VID -name $CLIENT-control -memory 2048 -sockets 1 -cores 4 -net0 e1000,bridge=vmbr0 -net1 e1000,bridge=$INTERFACE -virtio0=virt:$VID/ubuntu14-control.qcow2'"

mkdir /mnt/virt/images/$VID
mv ubuntu_qemu/$DRIVE.qcow2 /mnt/virt/images/$VID/

ssh root@$NODE bash -c "'pvesh create /nodes/$HOSTNAME/qemu/$VID/status/start'"
}

function newint {
ssh root@$NODE bash -c "'echo \"auto $INTERFACE  
iface $INTERFACE inet manual 
   bridge_ports none 
   bridge_stp off 
   bridge_fd 0\" >> /etc/network/interfaces' && ifup $INTERFACE"


}



usage()
{
cat << EOF
usage: $0 options

Sysprep images to prepare for upload to virt server

OPTIONS:
   -h      Show this message
   -c      client name
   -v      VID for new machine id on proxmox server
   -r      role [worker|DB|control|all]
   -n      node for virtual machine to live on
   -i      new interface name (or an existing for workers)

If "-r all" is chosen, then the VID will increment by 1 for each machine

ex. proxmox.sh -c newclient -v 200 -r all -n node1 -i vmbr200

EOF
}

VID=
ROLE=
NODE=
CLIENT=
INTERFACE=
while getopts “hc:i:v:n:r:” OPTION
do
     case $OPTION in
         h)
             usage
             exit 1
             ;;
         c)
             CLIENT=$OPTARG
             ;;         
         v)
             VID=$OPTARG
             ;;
         r)
             ROLE=$OPTARG
             ;;
         n)
             NODE=$OPTARG
             ;;
         i)
             INTERFACE=$OPTARG
             ;;
         ?)
             usage
             exit
             ;;
     esac
done

if [[ -z $VID ]] || [[ -z $ROLE ]] || [[ -z $NODE ]] || [[ -z $CLIENT ]] || [[ -z $INTERFACE ]]
then
     usage
     exit 1
fi



if [[ $ROLE =~ "worker" ]]; then
    worker
elif [[ $ROLE =~ "DB" ]]; then
    DB
elif [[ $ROLE =~ "control" ]]; then
    control
elif [[ $ROLE =~ "all" ]]; then
    newint
    DB
    VID=$(($VID+1))
    worker
    VID=$(($VID+1))
    control 
else
    usage
    exit 1
fi
