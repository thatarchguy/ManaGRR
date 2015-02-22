#!/bin/bash
# Configure the machine on firstboot according to its role.
# This should be installed on the machine during sysprep.sh

HOSTNAME=$HOSTNAME

function worker {

# Initalize network
# eth0 is the internal segment
# eth1 is an internet facing network for installing software
cat > /etc/network/interfaces << EOF
auto eth0
iface eth0 inet dhcp

auto eth1
iface eth1 inet dhcp

EOF

ifdown eth0 && ifup eth0
ifdown eth1 && ifup eth1

stdpkg

/bin/bash ./install_script_ubuntu.sh -y

/bin/bash /usr/share/grr/scripts/initctl_switch.sh multi

source /usr/share/grr/scripts/shell_helpers.sh

service grr-http-server stop    # This is 8080
service grr-ui stop             # This is 8000 address & 44449
service grr-enroller stop       # This is 44442
service grr-worker stop
service mongodb stop

echo "Mongo.server: 10.0.5.2" >> /etc/grr/server.local.yaml

service grr-worker start
}

function DB {

# Initalize network
# eth0 is the internal segment
# eth1 is an internet facing network for installing software
cat > /etc/network/interfaces << EOF
auto eth0
iface eth0 inet static
        address 10.0.5.2
        netmask 255.255.255.0

auto eth1
iface eth1 inet dhcp

EOF

ifdown eth0 && ifup eth0
ifdown eth1 && ifup eth1

apt-get update && apt-get install -y isc-dhcp-server
 
sed -i 's/INTERFACES=""/INTERFACES="eth0"/' /etc/default/isc-dhcp-server
sed -i 's/#authoritative/authoritative/' /etc/dhcp/dhcpd.conf
echo "subnet 10.0.5.0 netmask 255.255.255.0 { range 10.0.5.3 10.0.5.254; }" >> /etc/dhcp/dhcpd.conf
service isc-dhcp-server restart

stdpkg

/bin/bash ./install_script_ubuntu.sh -y

/bin/bash /usr/share/grr/scripts/initctl_switch.sh multi

service grr-http-server stop    # This is 8080
service grr-ui stop             # This is 8000 address & 44449
service grr-enroller stop       # This is 44442
service grr-worker stop
service mongodb stop

echo "Mongo.server: 10.0.5.2" >> /etc/grr/server.local.yaml
sed -i 's/bind_ip = 127.0.0.1/bind_ip = 10.0.5.2/' /etc/mongodb.conf

service mongodb start

}

function control {

# Initalize network
# eth1 is the internal segment
# eth0 is an internet facing network for installing software
cat > /etc/network/interfaces << EOF
auto eth0
iface eth0 inet dhcp

auto eth1
iface eth1 inet dhcp

EOF

ifdown eth0 && ifup eth0
ifdown eth1 && ifup eth1

stdpkg

/bin/bash ./install_script_ubuntu.sh -y

/bin/bash /usr/share/grr/scripts/initctl_switch.sh multi

source /usr/share/grr/scripts/shell_helpers.sh

service grr-http-server stop    # This is 8080
service grr-ui stop             # This is 8000 address & 44449
service grr-enroller stop       # This is 44442
service grr-worker stop
service mongodb stop

echo "Mongo.server: 10.0.5.2" >> /etc/grr/server.local.yaml
echo "AdminUI.url: http://0.0.0.0:8000" >> /etc/grr/server.local.yaml
echo "Monitoring.alert_email: grr-monitoring@example.com" >> /etc/grr/server.local.yaml
echo "Monitoring.emergency_access_email: grr-emergency@example.com" >> /etc/grr/server.local.yaml
echo "Client.control_urls: http://0.0.0.0:8080/control" >> /etc/grr/server.local.yaml
echo "Logging.domain: example.com" >> /etc/grr/server.local.yaml
echo "ClientBuilder.executables_path: /usr/share/grr/executables" >> /etc/grr/server.local.yaml
echo "Client.name: grr" >> /etc/grr/server.local.yaml
grr_config_updater generate_keys
grr_config_updater repack_clients
grr_config_updater update_user --password s3cur3password admin
grr_config_updater load_memory_drivers

service grr-http-server start    # This is 8080
service grr-ui start             # This is 8000 address & 44449
service grr-enroller start       # This is 44442
}

function stdpkg {

# install standard packages
/usr/sbin/dpkg-reconfigure openssh-server
}


if [[ $HOSTNAME == *DB ]]; then
    DB
elif [[ $HOSTNAME == *worker ]]; then
    worker
elif [[ $HOSTNAME == *control ]]; then
    control
fi

