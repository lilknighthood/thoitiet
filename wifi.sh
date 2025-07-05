#!/data/data/com.termux/files/usr/bin/bash

echo "=== Thiết lập môi trường WiFi hacking trên Termux ==="
echo "Cảnh báo: Script này dành cho mục đích học tập và kiểm thử bảo mật"
echo ""

# Kiểm tra quyền root
if [ "$EUID" -ne 0 ] && ! command -v tsu >/dev/null 2>&1; then
    echo "Cảnh báo: Cần quyền root để chạy các lệnh WiFi"
    echo "Hãy đảm bảo thiết bị đã được root và cài đặt tsu"
fi

# Cập nhật và nâng cấp packages
echo "Đang cập nhật packages..."
yes | pkg update
yes | pkg upgrade

# Cài đặt Python và các packages cơ bản
echo "Đang cài đặt Python và tools cơ bản..."
yes | pkg install python
yes | pkg install root-repo git tsu openssl

# Cài đặt các gói có sẵn
echo "Đang cài đặt các tools có sẵn..."
pkg install -y aircrack-ng 2>/dev/null || echo "aircrack-ng không khả dụng"

# Thử cài đặt các gói khác (có thể không khả dụng)
echo "Đang thử cài đặt các tools khác..."
pkg install -y wpa-supplicant 2>/dev/null || echo "wpa-supplicant không khả dụng trong Termux"
pkg install -y pixiewps 2>/dev/null || echo "pixiewps không khả dụng trong Termux"  
pkg install -y iw 2>/dev/null || echo "iw không khả dụng trong Termux"

# Cài đặt pip packages (bỏ qua việc upgrade pip)
echo "Đang cài đặt Python packages..."
python -m pip install pycryptodome psutil

# Clone repository nếu chưa có
echo "Đang clone repository..."
if [ ! -d "thoitiet" ]; then
    git clone https://github.com/lilknighthood/thoitiet.git
fi

# Chuyển vào thư mục
cd thoitiet

# Kiểm tra xem file có tồn tại không
if [ ! -f "thoitiet.py" ]; then
    echo "Lỗi: Không tìm thấy file thoitiet.py"
    exit 1
fi

chmod +x thoitiet.py

echo ""
echo "=== Thông tin quan trọng ==="
echo "1. Một số tools WiFi có thể không hoạt động trên Android do giới hạn kernel"
echo "2. Cần thiết bị đã root và hỗ trợ monitor mode"
echo "3. Không phải tất cả WiFi adapter đều hỗ trợ monitor mode trên Android"
echo ""

# Hiển thị thông tin về việc chạy
echo "Để chạy tool, sử dụng một trong các lệnh sau:"
echo "1. Với tsu (nếu có root): tsu python thoitiet.py -i wlan0 -K"
echo "2. Với sudo (nếu có): sudo python thoitiet.py -i wlan0 -K"
echo "3. Chạy trực tiếp: python thoitiet.py -i wlan0 -K"
echo ""

# Hỏi người dùng có muốn chạy ngay không
read -p "Bạn có muốn chạy tool ngay bây giờ? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Đang chạy tool..."
    if command -v tsu >/dev/null 2>&1; then
        tsu python thoitiet.py -i wlan0 -K
    else
        echo "Không tìm thấy tsu, thử chạy với sudo..."
        sudo python thoitiet.py -i wlan0 -K 2>/dev/null || {
            echo "Không thể chạy với sudo, chạy với quyền thường..."
            python thoitiet.py -i wlan0 -K
        }
    fi
else
    echo "Script đã hoàn thành. Bạn có thể chạy tool thủ công sau."
fi
