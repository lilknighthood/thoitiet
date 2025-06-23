#!/bin/bash

# Termux Setup Script
# Cập nhật và nâng cấp hệ thống

echo "=== Bắt đầu cập nhật hệ thống ==="
pkg update && pkg upgrade -y

echo "=== Cài đặt root repository ==="
pkg install root-repo -y

echo "=== Cài đặt pycryptodome ==="
pip install pycryptodome

echo "=== Cài đặt các gói cần thiết ==="
pkg install git tsu python wpa-supplicant pixiewps iw openssl -y

echo "=== Clone repository thoitiet ==="
git clone https://github.com/Thaomtam/thoitiet.git

echo "=== Di chuyển vào thư mục và thiết lập quyền ==="
cd thoitiet
chmod +x thoitiet.py

echo "=== Chạy ứng dụng ==="
sudo python thoitiet.py -i wlan0 -K
