##ManaGRR ![python 2.7](http://b.repl.ca/v1/python-2.7-blue.png) [![Issues in Ready](https://badge.waffle.io/thatarchguy/GRR-Manager.svg?label=ready&title=Ready)](http://waffle.io/thatarchguy/GRR-Manager) [![Build Status](https://travis-ci.org/thatarchguy/GRR-Manager.svg)](https://travis-ci.org/thatarchguy/GRR-Manager) 
----
A framework for creating and managing GRR clusters 

Utilizes proxmox as the hypervisor.

[Ideally done with Docker containers instead](https://github.com/google/grr/pull/124).
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


### The Setup
---
#### Prep servers
Get ssh keys installed for a root user on the proxmox server. 
This application ssh's into the server to provision VM's.

Mount the proxmox shares locally. 
Currently I'm using my NAS as storage for proxmox, so I just mounted the shares on my filesystem as /mnt/proxmox/ .

You may have to edit app/provision/provision.py to fit your layout.


#### Create Base image for roles
Go into the managrr/provision folder and create a packer image. 
The template .json file should be a fine start. Check the seedfile in httpdir as well
```
packer build qemu-ubuntu15.json
```

You can test the individual legacy scripts to make sure they run properly.

sysprep.sh then proxmox.sh

Once this is all verified worked, then run the application.



### How to Run:
---
It's still a jumble...

Docker, Vagrant, or virtualenv

```
# Install deps
pip install -r requirements.txt

# Create the sqlite database
python manage.py createdb
# OR
python manage.py db init
python manage.py db migrate
python manage.py db upgrade

# Run the program in server mode
python manage.py runserver --host=0.0.0.0

# Run a python shell in the program's context
python manage.py shell

# Start a worker (needed to provision)
python worker.py
```


## Screenshots
![ManaGRR Dashboard](docs/images/ManaGRR_Dash.png?raw=true)
![ManaGRR ClientAdmin](docs/images/ManaGRR_ClientAdmin.png?raw=true)
![ManaGRR AddClient](docs/images/ManaGRR_AddClient.png?raw=true)
![ManaGRR ClientList](docs/images/ManaGRR_ClientList.png?raw=true)
![ManaGRR HyperList](docs/images/ManaGRR_HyperList.png?raw=true)
