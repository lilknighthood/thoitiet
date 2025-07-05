#!/data/data/com.termux/files/usr/bin/bash

# Cập nhật và nâng cấp packages
yes | pkg update
yes | pkg upgrade

# Cài đặt Python và các packages cần thiết
yes | pkg install python
yes | pkg install root-repo git tsu wpa-supplicant pixiewps iw openssl

# Cài đặt pip packages (bỏ qua việc upgrade pip)
# python -m pip install --upgrade pip  # Dòng này gây lỗi trong Termux
python -m pip install pycryptodome psutil

# Clone repository nếu chưa có
if [ ! -d "thoitiet" ]; then
    git clone https://github.com/lilknighthood/thoitiet.git
fi

# Chuyển vào thư mục và chạy
cd thoitiet

chmod +x thoitiet.py

# Chạy script với quyền root
if command -v tsu >/dev/null 2>&1; then
    tsu python thoitiet.py -i wlan0 -K
else
    sudo python thoitiet.py -i wlan0 -K
fi
