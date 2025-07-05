#!/data/data/com.termux/files/usr/bin/bash

yes | pkg update
yes | pkg upgrade

# Cài python và pip (pip nằm trong gói python trên Termux)
yes | pkg install python

# Cài các package cần thiết
yes | pkg install root-repo git tsu wpa-supplicant pixiewps iw openssl

# Nâng cấp pip
pip install --upgrade pip

# Cài các thư viện python cần thiết
pip install pycryptodome psutil

# Clone repo nếu chưa tồn tại
if [ ! -d "thoitiet" ]; then
    git clone https://github.com/lilknighthood/thoitiet.git
fi

cd thoitiet

chmod +x thoitiet.py

# Chạy script với quyền root (nếu cần)
if command -v tsu >/dev/null 2>&1; then
    tsu python thoitiet.py -i wlan0 -K
else
    sudo python thoitiet.py -i wlan0 -K
fi
