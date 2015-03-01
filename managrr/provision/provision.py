"""
Class for deploying nodes
"""
from managrr import models, db, app
from sh import virt_sysprep, virt_copy_in, ssh, mkdir
from shutil import copyfile, move
import datetime

class ClientClass:

    def __init__(self, client):
        self.client = client
        self.hypervisorIP = models.Hypervisors.query.get(client.hyperv_id).IP
        lastVid = models.Nodes.query.order_by(models.Nodes.vid.desc()).filter_by(active=True).first()
        if lastVid is None:
            self.vid = 200
        else:
            self.vid = lastVid.vid + 1

        lastInterface = models.Nodes.query.order_by(models.Nodes.net.desc()).filter_by(active=True).first()
        if lastInterface is None:
            self.inter = "vmbr10"
        else:
            inter = str(lastInterface.net)
            interid = re.split('(\d+)', inter)
            self.inter = "vmbr" + str(int(interid[1]) + 1)
        app.logger.info("ClientClass initiated for: " + client.name)

    def build_base(self):
        app.logger.info("Building: all for newclient " + self.client.name)
        
        app.logger.info("Sysprepping " + self.client.name + ": DB")
        copyfile("deploy/ubuntu_qemu/qemu-ubuntu14-base.qcow2", "deploy/ubuntu_qemu/ubuntu14-" + self.client.name + "-DB.qcow2")
        virt_sysprep("-a", "deploy/ubuntu_qemu/ubuntu14-" + self.client.name + "-DB.qcow2")
        virt_copy_in("-a", "deploy/ubuntu_qemu/ubuntu14-" + self.client.name + "-DB.qcow2", "deploy/configure.sh", "/")
        virt_copy_in("-a", "deploy/ubuntu_qemu/ubuntu14-" + self.client.name + "-DB.qcow2", "deploy/grr_install/install_script_ubuntu.sh", "/")
        
        virt_sysprep("--enable", "customize", "--root-password", "password:s3cur3password", "--firstboot", "deploy/configure.sh", "--hostname", self.client.name + "-DB", "-a", "deploy/ubuntu_qemu/ubuntu14-" + self.client.name + "-DB.qcow2")
 
        app.logger.info("Sysprepping " + self.client.name + ": Control")
        copyfile("deploy/ubuntu_qemu/qemu-ubuntu14-base.qcow2", "deploy/ubuntu_qemu/ubuntu14-" + self.client.name + "-control.qcow2")
        virt_sysprep("-a", "deploy/ubuntu_qemu/ubuntu14-" + self.client.name + "-control.qcow2")
        virt_copy_in("-a", "deploy/ubuntu_qemu/ubuntu14-" + self.client.name + "-control.qcow2", "deploy/configure.sh", "/")
        virt_copy_in("-a", "deploy/ubuntu_qemu/ubuntu14-" + self.client.name + "-control.qcow2", "deploy/grr_install/install_script_ubuntu.sh", "/")
        
        virt_sysprep("--enable", "customize", "--root-password", "password:s3cur3password", "--firstboot", "deploy/configure.sh", "--hostname", self.client.name + "-control", "-a", "deploy/ubuntu_qemu/ubuntu14-" + self.client.name + "-control.qcow2")
        
        
        app.logger.info("Sysprepping " + self.client.name + ": Worker")
        copyfile("deploy/ubuntu_qemu/qemu-ubuntu14-base.qcow2", "deploy/ubuntu_qemu/ubuntu14-" + self.client.name + "-worker.qcow2")
        virt_sysprep("-a", "deploy/ubuntu_qemu/ubuntu14-" + self.client.name + "-worker.qcow2")
        virt_copy_in("-a", "deploy/ubuntu_qemu/ubuntu14-" + self.client.name + "-worker.qcow2", "deploy/configure.sh", "/")
        virt_copy_in("-a", "deploy/ubuntu_qemu/ubuntu14-" + self.client.name + "-worker.qcow2", "deploy/grr_install/install_script_ubuntu.sh", "/")
        
        virt_sysprep("--enable", "customize", "--root-password", "password:s3cur3password", "--firstboot", "deploy/configure.sh", "--hostname", self.client.name + "-worker", "-a", "deploy/ubuntu_qemu/ubuntu14-" + self.client.name + "-worker.qcow2")

        # Create network interface
        ssh("root@192.168.1.15", "echo \"auto " + self.inter + "\niface " +  self.inter + " inet manual\n\tbridge_ports none\n\tbridge_stp off\n\tbridge_fd 0\" >> /etc/network/interfaces && ifup " + self.inter)

        # Provision to hypervisoru
        app.logger.info("Provisioning to Hypervisor: " + self.client.name + "DB")
        vid = str(self.vid)
        hostname = str(ssh("root@" + self.hypervisorIP, "cat /etc/hostname").rstrip())
        ssh("root@" + self.hypervisorIP, "pvesh create /nodes/" + hostname + "/qemu -vmid " + vid + " -name " + self.client.name + "-DB -memory 2048 -sockets 2 -cores 4 -net0 e1000,bridge=" + self.inter + " -net1 e1000,bridge=vmbr1 -virtio0=virt:" + vid + "/ubuntu14-" + self.client.name + "-DB.qcow2")
        mkdir("/mnt/virt/images/" + vid)
        move("deploy/ubuntu_qemu/ubuntu14-" + self.client.name + "-DB.qcow2", "/mnt/virt/images/" + vid)
        ssh("root@" + self.hypervisorIP, "pvesh create /nodes/" + hostname + "/qemu/" + vid + "/status/start")


        app.logger.info("Provisioning to Hypervisor: " + self.client.name + "control")
        vid = str(self.vid + 1)
        hostname = str(ssh("root@" + self.hypervisorIP, "cat /etc/hostname").rstrip())
        ssh("root@" + self.hypervisorIP, "pvesh create /nodes/" + hostname + "/qemu -vmid " + vid + " -name " + self.client.name + "-control -memory 2048 -sockets 2 -cores 4 -net0 e1000,bridge=" + self.inter + " -net1 e1000,bridge=vmbr1 -virtio0=virt:" + vid + "/ubuntu14-" + self.client.name + "-control.qcow2")
        mkdir("/mnt/virt/images/" + vid)
        move("deploy/ubuntu_qemu/ubuntu14-" + self.client.name + "-control.qcow2", "/mnt/virt/images/" + vid)
        ssh("root@" + self.hypervisorIP, "pvesh create /nodes/" + hostname + "/qemu/" + vid + "/status/start")


        app.logger.info("Provisioning to Hypervisor: " + self.client.name + "worker")
        vid = str(self.vid + 2)
        hostname = str(ssh("root@" + self.hypervisorIP, "cat /etc/hostname").rstrip())
        ssh("root@" + self.hypervisorIP, "pvesh create /nodes/" + hostname + "/qemu -vmid " + vid + " -name " + self.client.name + "-worker -memory 2048 -sockets 2 -cores 4 -net0 e1000,bridge=" + self.inter + " -net1 e1000,bridge=vmbr1 -virtio0=virt:" + vid + "/ubuntu14-" + self.client.name + "-worker.qcow2")
        mkdir("/mnt/virt/images/" + vid)
        move("deploy/ubuntu_qemu/ubuntu14-" + self.client.name + "-worker.qcow2", "/mnt/virt/images/" + vid)
        ssh("root@" + self.hypervisorIP, "pvesh create /nodes/" + hostname + "/qemu/" + vid + "/status/start")

        # Add to database
        addDatabase = models.Nodes(client_id=self.client.id, type="database", date_added=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), location="proxmox", IP="0.0.0.0", net=self.inter, vid=self.vid)
        addControl  = models.Nodes(client_id=client.id, type="control", date_added=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), location="proxmox", IP="0.0.0.0", net=self.inter, vid=self.vid + 1)
        addWorker   = models.Nodes(client_id=client.id, type="worker", date_added=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), location="proxmox", IP="0.0.0.0", net=self.inter, vid=self.vid + 2)
        db.session.add(addDatabase)
        db.session.add(addControl)
        db.session.add(addWorker)
        db.session.commit()
    
        return True



    def build_worker_local(self):
        app.logger.info("Sysprepping " + self.client.name + ": Worker")
        copyfile("deploy/ubuntu_qemu/qemu-ubuntu14-base.qcow2", "deploy/ubuntu_qemu/ubuntu14-" + self.client.name + "-worker.qcow2")
        virt_sysprep("-a", "deploy/ubuntu_qemu/ubuntu14-" + self.client.name + "-worker.qcow2")
        virt_copy_in("-a", "deploy/ubuntu_qemu/ubuntu14-" + self.client.name + "-worker.qcow2", "deploy/configure.sh", "/")
        virt_copy_in("-a", "deploy/ubuntu_qemu/ubuntu14-" + self.client.name + "-worker.qcow2", "deploy/grr_install/install_script_ubuntu.sh", "/")
        
        virt_sysprep("--enable", "customize", "--root-password", "password:s3cur3password", "--firstboot", "deploy/configure.sh", "--hostname", self.client.name + "-worker", "-a", "deploy/ubuntu_qemu/ubuntu14-" + self.client.name + "-worker.qcow2")
        
        lastVid = models.Nodes.query.order_by(models.Nodes.vid.desc()).filter_by(active=True).first()
        if lastVid is None:
            vid = "200"
        else:
            vid = str(lastVid.vid + 1)

        app.logger.info("Building: worker for " + self.client.name)

        # Provision to hypervisor
        hostname = str(ssh("root@" + self.hypervisorIP, "cat /etc/hostname").rstrip())
        ssh("root@" + self.hypervisorIP, "pvesh create /nodes/" + hostname + "/qemu -vmid " + vid + " -name " + self.client.name + "-control -memory 2048 -sockets 2 -cores 4 -net0 e1000,bridge=" + self.inter + " -net1 e1000,bridge=vmbr1 -virtio0=virt:" + vid + "/ubuntu14-" + self.client.name + "-control.qcow2")
        mkdir("/mnt/virt/images/" + vid)
        move("deploy/ubuntu_qemu/ubuntu14-" + self.client.name + "-control.qcow2", "/mnt/virt/images/" + vid)
        ssh("root@" + self.hypervisorIP, "pvesh create /nodes/" + hostname + "/qemu/" + vid + "/status/start")

        # Add to Database
        addWorker = models.Nodes(client_id=client.id, type="worker", date_added=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), location="proxmox", IP="0.0.0.0", net=inter, vid=vid)
        db.session.add(addWorker)
        db.session.commit() 
        return True

    
    def build_worker_digiocean(self, key):
        app.logger.info("build_client_digiocean " + str(client.id) + key)
        return True


    def build_worker_aws(self, key):
        app.logger.info("build_client_aws " + str(client.id) + key)

        return True

