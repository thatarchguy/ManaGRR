##grrmanager [![Issues in Ready](https://badge.waffle.io/thatarchguy/GRR-Manager.svg?label=ready&title=Ready)](http://waffle.io/thatarchguy/GRR-Manager) [![Build Status](https://travis-ci.org/thatarchguy/GRR-Manager.svg)](https://travis-ci.org/thatarchguy/GRR-Manager) 
----
A framework for managing GRR clusters 

### Current build
---
Currently in heavy development
0.0.0a

Requirements:
 - python2.7
 - http://packer.io
 - libguestfs


I'm testing on Arch Linux
 - Python 2.7.9
 - packer-io-git 0.7.2.r23.ga559296-1
 - libguestfs 1.28.2-1


### The Process
---
#### Prep servers
Get ssh keys installed for a root user on the proxmox server. 
This application ssh's into the server to provision VM's.

Mount the proxmox shares locally. 
Currently I'm using my NAS as storage for proxmox, so I just mounted the shares on my filesystem as /mnt/virt/ .

You will have to edit app/provision/proxmox.sh to fit your layout.


#### Create Base image for roles
Go into the app/provision folder and create a packer image. 
The template .json file should be a fine start. Check the seedfile in httpdir as well
```
packer build qemu-ubuntu15.json
```

You can test the individual scripts to make sure they run properly.

sysprep.sh then proxmox.sh


Once this is all verified worked, then run the application.



### How to Run:
---
It's still a jumble...

Docker, vagrant, or make env

```
pip install requirements.txt

# Create the sqlite database
python -m scripts.db_create
python -m scripts.db_migrate

python run.py
```



