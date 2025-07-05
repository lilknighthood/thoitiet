pkg update && pkg upgrade -y
pkg install root-repo -y
pip install pycryptodome
pip install psutil (nếu sài thoitietv2.py)
pkg install git tsu python wpa-supplicant pixiewps iw openssl -y
git clone https://github.com/lilknighthood/thoitiet.git
cd thoitiet
chmod +x thoitiet.py
sudo python thoitiet.py -i wlan0 -K
