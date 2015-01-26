#!/bin/bash

usage()
{
cat << EOF
usage: $0 options

wrapper for flask application to run sysprep and upload 

OPTIONS:
   -h      Show this message
   -c      client name
   -b      client ID
   -v      VID for new machine id on proxmox server
   -r      role [worker|DB|control|all]
   -n      node for virtual machine to live on
   -i      new interface name (or an existing for workers)

If "-r all" is chosen, then the VID will increment by 1 for each machine

ex. wrapper.sh -c newclient -b 13 -v 200 -r all -n node1 -i vmbr200

EOF
}

VID=
ROLE=
NODE=
CLIENT=
CID=
INTERFACE=
while getopts “hc:i:b:v:n:r:” OPTION
do
     case $OPTION in
         h)
             usage
             exit 1
             ;;
         c)
             CLIENT=$OPTARG
             ;; 
         b)
             CID=$OPTARG
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

if [[ -z $VID ]] || [[ -z $ROLE ]] || [[ -z $NODE ]] || [[ -z $CLIENT ]] || [[ -z $INTERFACE ]] || [[ -z $CID ]]
then
     usage
     exit 1
fi

if [ -f $CID.lockfile ] || [ -f $CID.worker.lockfile ]; then
    exit 1
fi



if [[ $ROLE =~ "worker" ]]; then
     echo "sysprep" > $CID.worker.lockfile
     ./sysprep.sh -c $CLIENT -r worker
     echo "proxmox" > $CID.worker.lockfile
     ./proxmox.sh -c $CLIENT -v $VID -r worker -n $NODE -i $INTERFACE
     echo "installing" > $CID.worker.lockfile
     rm -f $CID.worker.lockfile
elif [[ $ROLE =~ "DB" ]]; then
     echo "sysprep" > $CID.lockfile
     ./sysprep.sh -c $CLIENT -r DB
     echo "proxmox" > $CID.lockfile
     ./proxmox.sh -c $CLIENT -v $VID -r DB -n $NODE -i $INTERFACE
     echo "installing" > $CID.lockfile
     rm -f $CID.lockfile
elif [[ $ROLE =~ "control" ]]; then
     echo "sysprep" > $CID.lockfile
     ./sysprep.sh -c $CLIENT -r control
     echo "proxmox" > $CID.lockfile
     ./proxmox.sh -c $CLIENT -v $VID -r control -n $NODE -i $INTERFACE
     echo "installing" > $CID.lockfile
     rm -f $CID.lockfile
elif [[ $ROLE =~ "all" ]]; then
     echo "sysprep" > $CID.lockfile
     ./sysprep.sh -c $CLIENT -r all
     echo "proxmox" > $CID.lockfile
     ./proxmox.sh -c $CLIENT -v $VID -r all -n $NODE -i $INTERFACE
     echo "installing" > $CID.lockfile
     rm -f $CID.lockfile
else
    usage
    exit 1
fi
