#######################################################
#!/bin/bash

#####Base Install Script For GRR Server #####

#######################################################
echo -n "Please enter a hostname for this machine :"

read user_hostname

hostname $user_hostname

HOSTNAME=$user_hostname

touch "/var/log/baseline.log"

HARD_LOG="/var/log/baseline.log"

echo "HOSTNAME:" $HOSTNAME >>$HARD_LOG

date >>$HARD_LOG

echo "Creating Backup of System Files"

mkdir /var/cache/baseline

tar -cvf /var/cache/baseline/etc.tar /etc &>/dev/null

echo "/etc/ has been backed up to /var/cache/baseline/etc.tar" >> $HARD_LOG

echo "/etc/ has been backed up to /var/cache/baseline/etc.tar"

######Banner#####

echo "Updating the banner in /etc/issue.net file" >> $HARD_LOG

echo "********************************************************************************" >/etc/issue.net

echo "* *">>/etc/issue.net

echo "* ATTENTION! PLEASE READ CAREFULLY. *">>/etc/issue.net

echo "* *">>/etc/issue.net

echo "* This system is the property of Champlain College. It is for authorized use only. *">>/etc/issue.net

echo "* Users have no explicit or implicit expectation *">>/etc/issue.net

echo "* of privacy. Any or all uses of this system and all files on the this system *">>/etc/issue.net

echo "* will be intercepted, monitored, recorded, copied, audited, inspected, and *">>/etc/issue.net

echo "* disclosed to Champlain College management, and law enforcement personnel as *">>/etc/issue.net

echo "* well as other authorized agencies. By using this system, the user consents *">>/etc/issue.net

echo "* to such interception,monitoring, recording, copying, auditing, inspection, *">>/etc/issue.net

echo "* and disclosure at the discretion of Champlain College. Unauthorized or improper *">>/etc/issue.net

echo "* use of this system may result in administrative disciplinary action and civil*">>/etc/issue.net

echo "* and criminal penalties. By continuing to use this system you indicate the *">>/etc/issue.net

echo "* awareness of and consent to these terms and conditions of use. LOG OFF *">>/etc/issue.net

echo "* IMMEDIATELY if you do not agree to the terms and conditions stated in this *">>/etc/issue.net

echo "* warning. *">>/etc/issue.net

echo "* *">>/etc/issue.net

echo "********************************************************************************">>/etc/issue.net

echo "/etc/issue.net Banner has been set"

#######motd#######

echo "Updating the banner in /etc/motd file" >>$HARD_LOG

echo "********************************************************************************" >/etc/motd

echo "* *">>/etc/motd>> ${HARD_LOG}

echo "* ATTENTION! PLEASE READ CAREFULLY. *">>/etc/motd

echo "* *">>/etc/motd

echo "* This system is the property of Champlain College. It is for authorized use only. *">>/etc/motd

echo "* Users  have no explicit or implicit expectation *">>/etc/motd

echo "* of privacy. Any or all uses of this system and all files on the this system *">>/etc/motd

echo "* will be intercepted, monitored, recorded, copied, audited, inspected, and *">>/etc/motd

echo "* disclosed to Champlain College, and law enforcement personnel as *">>/etc/motd

echo "* well as other authorized agencies. By using this system, the user consents *">>/etc/motd

echo "* to such interception,monitoring, recording, copying, auditing, inspection, *">>/etc/motd

echo "* and disclosure at the discretion of Champlain College. Unauthorized or improper *">>/etc/motd

echo "* use of this system may result in administrative disciplinary action and civil*">>/etc/motd

echo "* and criminal penalties. By continuing to use this system you indicate the *">>/etc/motd

echo "* awareness of and consent to these terms and conditions of use. LOG OFF *">>/etc/motd

echo "* IMMEDIATELY if you do not agree to the terms and conditions stated in this *">>/etc/motd

echo "* warning. *">>/etc/motd

echo "* *">>/etc/motd

echo "********************************************************************************">>/etc/motd

echo "/etc/motd Banner Updated" >>$HARD_LOG

echo "/etc/motd Banner has been updated"


#####ssh configuration######

echo "Configuring SSH service" >>$HARD_LOG



cp -p sshd_config /var/cache/baseline/sshd_config.bk

sed -i "s/#PermitEmptyPasswords no/PermitEmptyPasswords no/g" /etc/ssh/sshd_config

sed -i "s/#PermitEmptyPasswords no/PermitEmptyPasswords no/g" /etc/ssh.sshd_config

sed -i "s/#Banner /etc/issue.net/Banner /etc/issue.net/g" /etc/ssh/sshd_config

echo "SSH Configuration Complete" >> $HARD_LOG

echo "SSH Configuration Complete"


########Install GRR#############

echo "Beginning GRR Install..."

sleep 3

bash ./grr_install_ubuntu.sh

echo "********************************************************************************"

echo "GRR Install Complete."

echo "GRR Installed" >>$HARD_LOG



