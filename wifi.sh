#!/data/data/com.termux/files/usr/bin/bash

yes | pkg update
yes | pkg upgrade
yes | pkg install python
yes | pkg install pip
yes | pkg install root-repo
pip install --upgrade pip
pip install pycryptodome
pip install psutil
yes | pkg install git tsu wpa-supplicant pixiewps iw openssl
git clone https://github.com/lilknighthood/thoitiet.git
cd thoitiet
chmod +x thoitiet.py
sudo python thoitiet.py -i wlan0 -K
