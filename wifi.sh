#!/data/data/com.termux/files/usr/bin/bash

yes | pkg update
yes | pkg upgrade
yes | pkg install python
yes | pkg install root-repo git tsu wpa-supplicant pixiewps iw openssl

python -m pip install --upgrade pip
python -m pip install pycryptodome psutil

if [ ! -d "thoitiet" ]; then
    git clone https://github.com/lilknighthood/thoitiet.git
fi

cd thoitiet

chmod +x thoitiet.py

if command -v tsu >/dev/null 2>&1; then
    tsu python thoitiet.py -i wlan0 -K
else
    sudo python thoitiet.py -i wlan0 -K
fi
