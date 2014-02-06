#!/bin/bash

###
#    @author: CarolinaFernandez
#    @organization: i2CAT
#    @project: Ofelia FP7
#    @description: script to install a specific FlowVisor release and configure according to our needs
###


# XXX: Move somewhere else
source ../utils/utils.sh

FLOWVISOR_RELEASE="1.4.0-1"

# If dpkg shows entry with $FLOWVISOR_RELEASE on it, do not install
if [[ $(dpkg -l | grep flowvisor) =~ $FLOWVISOR_RELEASE ]]; then
    warning "FlowVisor $FLOWVISOR_RELEASE already installed. Skipping..."
    exit 1
fi

# Otherwise, ask for confirmation on the installation of FlowVisor
# and warn about compatibility issues
accept_deploy_flowvisor=0
while [[ ! $accept_deploy_flowvisor =~ ^[y|Y|n|N]$ ]]
    do
        print_header "Do you wish to install FlowVisor $FLOWVISOR_RELEASE?"
        warning " Notice that you *must* use FOAM with this."
        warning " Notice that if you already installed a FlowVisor non-versioned in the Debian package system, you should consider backing up and transferring your current flowspaces, if any."
        print " > If you want to keep using Opt-in please press \"n\"\n > If you want to keep the flowspaces at your current FlowVisor and are not able to backup these, please press \"n\""
        print "[y/N]"
        read accept_deploy_flowvisor
        if [[ ! $accept_deploy_flowvisor =~ ^[y|Y|n|N]$ ]]; then
            print "Please accept (\"y\") or reject (\"n\") the installation"
        fi
        if [[ $accept_deploy_flowvisor =~ ^[n|N]$ ]]; then
            warning "FlowVisor installation aborted by user"
            exit 1
        fi
    done

# Obtain public repository key, install it, remove it
wget http://updates.onlab.us/GPG-KEY-ONLAB
apt-key add GPG-KEY-ONLAB
rm GPG-KEY-ONLAB

# Add the following line to /etc/apt/sources.list (if not already there)
if [[ ! $(grep "deb http://updates.onlab.us/debian" /etc/apt/sources.list | grep -v "^#") ]]; then
    echo """
#
# FlowVisor at ON.LAB
#
## Release - the latest and greatest
deb     http://updates.onlab.us/debian stable/
# Staging - what's coming next
deb     http://updates.onlab.us/debian staging/
# Nightly - the bleeding edge
deb     http://updates.onlab.us/debian unstable/""" >> /etc/apt/sources.list
fi

# Update your apt database
apt-get update

# Install sudo package to be able to run some commands at FlowVisor initscript
apt-get -y install sudo
# Install chosen version of FlowVisor
apt-get -y install flowvisor=$FLOWVISOR_RELEASE

# Generate new configuration and load it
if [[ ! -f /etc/flowvisor/config.json ]]; then
    fvconfig generate /etc/flowvisor/config.json
fi
fvconfig load /etc/flowvisor/config.json

# Modify to meet our requirements
# Correct permissions in order to be able to pass this point and write to the DB
chown flowvisor:flowvisor /usr/share/db/flowvisor -R
chown flowvisor:flowvisor /etc/flowvisor -R
chmod 755 /usr/share/db/flowvisor/derby.log
# Modify log configuration to avoid writing on stdout
sed -i -e "s/^log4j.rootCategory=WARN, system/#log4j.rootCategory=WARN, system\nlog4j.rootCategory=WARN/" /etc/flowvisor/fvlog.config

# Start FlowVisor
/etc/init.d/flowvisor restart

success "FlowVisor successfully installed"
