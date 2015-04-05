#!/bin/bash
# Delete node from hypervisor


function worker {
ssh root@$NODE bash -c "'
qm stop $VID && qm destroy $VID --skiplock'"

ssh root@$NODE bash -c "'rm -rf /mnt/pve/virt/images/$VID'"

}

function DB {

ssh root@$NODE bash -c "'
qm stop $VID && qm destroy $VID --skiplock'"

ssh root@$NODE bash -c "'rm -rf /mnt/pve/virt/images/$VID'"

}

function control {

ssh root@$NODE bash -c "'
qm stop $VID && qm destroy $VID --skiplock'"

ssh root@$NODE bash -c "'rm -rf /mnt/pve/virt/images/$VID'"

}

function delint {
ssh root@$NODE bash <<EOF
sed -i '/$INTERFACE/, +4d' /etc/network/interfaces 
service networking restart

EOF

}



usage()
{
cat << EOF
usage: $0 options

Delete on hypervisor

OPTIONS:
   -h      Show this message
   -v      VID for new machine id on proxmox server
   -r      role [worker|DB|control|all]
   -n      node for virtual machine to live on
   -i      interface name 

If "-r all" is chosen, then the VID will increment by 1 for each machine

ex. delete.sh -v 200 -r all -n node1 -i vmbr200

EOF
}

VID=
ROLE=
NODE=
INTERFACE=
while getopts “hi:v:n:r:” OPTION
do
     case $OPTION in
         h)
             usage
             exit 1
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

if [[ -z $VID ]] || [[ -z $ROLE ]] || [[ -z $NODE ]] || [[ -z $INTERFACE ]]
then
     usage
     exit 1
fi



if [[ $ROLE =~ "worker" ]]; then
    worker
elif [[ $ROLE =~ "database" ]]; then
    DB
elif [[ $ROLE =~ "control" ]]; then
    control
    delint
else
    usage
    exit 1
fi
