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
}

function stdpkg {

# install standard packages
/usr/sbin/dpkg-reconfigure openssh-server
}


if [[ $HOSTNAME =~ [/DB/] ]]; then
    DB
elif [[ $HOSTNAME =~ [/worker/] ]]; then
    worker
elif [[ $HOSTNAME =~ [/control/] ]]; then
    control
fi

