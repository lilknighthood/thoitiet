# thoitiet
Crack wps wifi

# Hướng dẫn sơ sài :
* pkg update && pkg upgrade -y
* pkg install root-repo -y
* pkg install python-pip
* pip install pycryptodome (hoặc pip install pybase64)
* pkg install git tsu python wpa-supplicant pixiewps iw openssl -y
* git clone https://github.com/lilknighthood/thoitiet.git
* cd thoitiet
* chmod +x thoitiet.py
* sudo python thoitiet.py -i wlan0 -K
* (Ở bước cuối cùng, nhớ tắt wifi khi scan wifi)
