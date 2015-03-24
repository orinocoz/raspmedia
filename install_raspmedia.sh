#!/bin/sh

echo "Removing not used wolfram engine..."
# remove not used wolfram-engine
sudo apt-get -y remove wolfram-engine;

echo "Updating sources and system..."
# update apt sources and upgrade installed packages
sudo apt-get -y update;
sudo apt-get -y upgrade;

echo "Installing required packages..."
# install apache webserver with php5
sudo apt-get -y install apache2 php5 libapache2-mod-php5;

# install python imaging library
sudo apt-get -y install python-imaging;

# install chromium browser with x11 utils and unclutter
sudo apt-get -y install chromium x11-xserver-utils unclutter;

# install usbmount, could be usable for future updates
sudo apt-get -y install usbmount;

# install netifaces
sudo apt-get -y install python-netifaces;

# install pexpect
sudo apt-get -y install python-pexpect;

# install commandline framebuffer image viewer
sudo apt-get -y install fbi;

# install mplayer
sudo apt-get -y install mplayer;

# install mediainfo library
sudo apt-get -y install mediainfo;

# install pip and psutil
echo "Installing package installer PIP...";
wget https://bootstrap.pypa.io/get-pip.py;
sudo python get-pip.py;
echo "Installing GCC and Python Headers...";
sudo apt-get -y install gcc python-dev;
echo "Installing PSUTIL...";
sudo pip install psutil;

echo "Installing PyOMXPlayer...";
# fetch files for pyomxplayer
cd /home/pi;
su -l pi -c 'git clone https://github.com/peter9teufel/working_py_omx.git';
# install pyomxplayer
cd /home/pi/working_py_omx;
sudo python setup.py install;

echo "";
echo "Cloning RaspMedia Player source from github";
# clone raspmedia sourcefiles to /home/pi/raspmedia
cd /home/pi;
su -l pi -c 'git clone https://github.com/peter9teufel/raspmedia.git';

echo "";
echo "Writing boot config...";
sudo cat /home/pi/raspmedia/raspmedia_boot_config.txt > /boot/config.txt;
echo "";

echo "Setting up autostart of RaspMedia Player";
# modify rc.local to start raspmedia at boot
sudo head -n -3 /etc/rc.local > /home/pi/rc.local.tmp;
sudo cat /home/pi/rc.local.tmp > /etc/rc.local;
sudo echo 'cd /home/pi/raspmedia/Raspberry' >> /etc/rc.local;
sudo echo 'sudo python raspmedia-usb-loader.py' >> /etc/rc.local;
sudo echo 'exit 0' >> /etc/rc.local;
sudo rm /home/pi/rc.local.tmp;

echo 'Setup complete!';
echo 'Rebooting...';
sudo reboot;

# install script deletes itself after completion
rm -- "$0"
