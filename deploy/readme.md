place seedfile in ./httpdir

$ packer build qemu-ubuntu15.json
 - This creates the base image using this config and the seedfile

managrr/provision/provision.py reads & writes in this directory


mount your proxmox share to /mnt/proxmox/
