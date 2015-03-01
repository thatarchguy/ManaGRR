place seedfile in ./httpdir

$ packer build qemu-ubuntu15.json
 - This creates the base image using this config and the seedfile

then run sysprep.sh 
 - that will take the base image and sysprep it, add the install script, and set the hostname
 
then run proxmox.sh
 - you will need ssh keys installed on the proxmox server 


managrr/provision/provision.py reads & writes in this directory
