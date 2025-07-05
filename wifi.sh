#!/data/data/com.termux/files/usr/bin/bash

echo "=== Thiết lập WiFi Hacking Tools trên Termux (Rooted) ==="
echo "Device: Rooted Android với Termux"
echo ""

# Cập nhật và nâng cấp packages
echo "[+] Đang cập nhật packages..."
yes | pkg update && yes | pkg upgrade

# Cài đặt packages cơ bản
echo "[+] Cài đặt Python và tools cơ bản..."
pkg install -y python git tsu openssl build-essential

# Cài đặt root-repo để có thêm tools
echo "[+] Cài đặt root-repo..."
pkg install -y root-repo

# Cài đặt các tools có sẵn
echo "[+] Cài đặt aircrack-ng..."
pkg install -y aircrack-ng || echo "[-] aircrack-ng không khả dụng"

# Thử cài đặt wpa-supplicant
echo "[+] Thử cài đặt wpa-supplicant..."
pkg install -y wpa-supplicant || echo "[-] wpa-supplicant không có trong repo"

# Cài đặt iw (wireless tools)
echo "[+] Thử cài đặt iw..."
pkg install -y iw || echo "[-] iw không có trong repo"

# Cài đặt pixiewps từ source vì không có trong repo
echo "[+] Biên dịch pixiewps từ source..."
if [ ! -d "pixiewps" ]; then
    git clone https://github.com/wiire-a/pixiewps.git
    cd pixiewps
    make || echo "[-] Lỗi biên dịch pixiewps"
    if [ -f "pixiewps" ]; then
        cp pixiewps $PREFIX/bin/
        echo "[+] pixiewps đã được cài đặt"
    else
        echo "[-] Không thể biên dịch pixiewps"
    fi
    cd ..
else
    echo "[+] pixiewps đã tồn tại"
fi

# Cài đặt Python packages
echo "[+] Cài đặt Python packages..."
python -m pip install pycryptodome psutil

# Clone repository
echo "[+] Clone repository thoitiet..."
if [ ! -d "thoitiet" ]; then
    git clone https://github.com/lilknighthood/thoitiet.git
else
    echo "[+] Repository thoitiet đã tồn tại"
fi

cd thoitiet

# Kiểm tra file
if [ ! -f "thoitiet.py" ]; then
    echo "[-] Lỗi: Không tìm thấy file thoitiet.py"
    exit 1
fi

chmod +x thoitiet.py

# Kiểm tra interface WiFi
echo "[+] Kiểm tra interface WiFi..."
ip link show | grep wlan || echo "[-] Không tìm thấy interface wlan"

# Kiểm tra tsu
if command -v tsu >/dev/null 2>&1; then
    echo "[+] tsu đã sẵn sàng"
else
    echo "[-] tsu không khả dụng"
    exit 1
fi

echo ""
echo "=== Thiết lập hoàn thành ==="
echo "[+] Tools đã cài đặt:"
echo "  - Python và pip packages"
echo "  - aircrack-ng (nếu có)"
echo "  - pixiewps (từ source)"
echo "  - tsu (root access)"
echo ""

# Hiển thị hướng dẫn
echo "=== Hướng dẫn sử dụng ==="
echo "1. Chạy với interface mặc định:"
echo "   tsu python thoitiet.py -i wlan0 -K"
echo ""
echo "2. Liệt kê các interface có sẵn:"
echo "   ip link show"
echo ""
echo "3. Kiểm tra monitor mode (nếu hỗ trợ):"
echo "   tsu iw dev wlan0 info"
echo ""

# Hỏi có muốn chạy ngay không
read -p "Bạn có muốn chạy tool ngay bây giờ? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "[+] Đang chạy tool với quyền root..."
    echo "Lệnh: tsu python thoitiet.py -i wlan0 -K"
    echo ""
    tsu python thoitiet.py -i wlan0 -K
else
    echo "[+] Thiết lập hoàn thành. Bạn có thể chạy tool thủ công:"
    echo "cd thoitiet && tsu python thoitiet.py -i wlan0 -K"
fi
