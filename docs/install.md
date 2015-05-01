## The Setup
---
#### Prep servers
Get ssh keys installed for a root user on the proxmox server.
This application ssh's into the server to provision VM's.

Mount the proxmox shares locally.
Currently I'm using my NAS as storage for proxmox, so I just mounted the shares on my filesystem as /mnt/proxmox/ .

You may have to edit app/provision/provision.py to fit your layout.


#### Create Base image for roles
Go into the deploy folder and create a packer image. You'll need a ubuntu iso file for this.
The template .json file should be a fine start. Check the seedfile in httpdir as well.
```
packer build qemu-ubuntu15.json
```

You can test the individual legacy scripts in managrr/provision/legacy/ to make sure they run properly.

sysprep.sh then proxmox.sh

Once this is all verified worked, then run the application.

#### Install Prerequisites
Install Redis, Python2.7 Packer-io, and libguestfs.  
There are packages for Debian and Arch based distributions.

### How to Run:
---

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

# Start a worker (needed to provision)
python worker.py
```


It should be running now. The default login is admin:managrr
