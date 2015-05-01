##ManaGRR ![python 2.7](http://b.repl.ca/v1/python-2.7-blue.png) [![Issues in Ready](https://badge.waffle.io/thatarchguy/GRR-Manager.svg?label=ready&title=Ready)](http://waffle.io/thatarchguy/GRR-Manager) [![Build Status](https://travis-ci.org/thatarchguy/GRR-Manager.svg)](https://travis-ci.org/thatarchguy/GRR-Manager) 
----
A framework for creating and managing GRR clusters 

Utilizes proxmox as the hypervisor.

This was written as a capstone project for Champlain College.   
[Blog Post](http://kevinlaw.info/blog/senior-capstone-managrr/)   
[Capstone Paper](docs/paper/Capstone_Final_KevinLaw.pdf?raw=true)  
[Capstone Poster](docs/paper/poster-kevin_law.pdf?raw=true)  

[Ideally done with Docker containers instead](https://github.com/google/grr/pull/124).
### Current build
---

Requirements:
 - python2.7
 - http://packer.io
 - libguestfs


I'm testing on Arch Linux
 - Python 2.7.9
 - packer-io-git 0.7.2.r23.ga559296-1
 - libguestfs 1.28.2-1

### Installation
See the [install.md page](docs/install.md)

### Contributing
See the [contribute.md page](docs/contribute.md)

## Screenshots
![ManaGRR Dashboard](docs/images/ManaGRR_Dash.png?raw=true)
![ManaGRR ClientAdmin](docs/images/ManaGRR_ClientAdmin.png?raw=true)
![ManaGRR AddClient](docs/images/ManaGRR_AddClient.png?raw=true)
![ManaGRR ClientList](docs/images/ManaGRR_ClientList.png?raw=true)
