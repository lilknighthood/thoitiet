#!/data/data/com.termux/files/usr/bin/bash
# Termux + Android (root) WiFi setup helper for thoitiet repo
# Ưu tiên chạy: sudo python thoitietv2.py -i <iface> -K
# Fallback: tsu -- / su -c / chạy thường
# Usage: bash wifi.sh [-d|--debug] [-i IFACE] [--no-py] [--no-psutil] [--branch BRANCH] [--no-run]

set -Eeuo pipefail

#####################################
# Màu sắc
#####################################
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

#####################################
# Biến mặc định
#####################################
IFACE="wlan0"
BRANCH="main"
INSTALL_PY=true
INSTALL_PSUTIL=true
RUN_AFTER_INSTALL=true
DEBUG=false
REPO_URL="https://github.com/lilknighthood/thoitiet.git"
REPO_DIR="thoitiet"

#####################################
# Tiện ích in
#####################################
info()    { echo -e "${YELLOW}[INFO]${NC} $*"; }
ok()      { echo -e "${GREEN}[OK]${NC} $*"; }
warn()    { echo -e "${CYAN}[NOTE]${NC} $*"; }
err()     { echo -e "${RED}[ERROR]${NC} $*"; }

trap 'err "Đã xảy ra lỗi ở dòng $LINENO. Dừng lại."' ERR

usage() {
  cat <<EOF
${GREEN}=== Trình cài đặt WiFi Tool cho Termux (Android root) ===${NC}

Tùy chọn:
  -d, --debug        In thông tin hệ thống & gỡ lỗi
  -i, --iface IFACE  Chỉ định interface WiFi (mặc định: wlan0)
      --no-py        Không cài gói Python (pip packages)
      --no-psutil    Không cài psutil
      --no-run       Không chạy thoitietv2.py sau khi cài
      --branch BR    Chỉ định nhánh git (mặc định: main)
  -h, --help         Hiển thị trợ giúp

Ví dụ:
  bash wifi.sh -d -i wlan0
  bash wifi.sh --branch main --no-run
EOF
}

debug_system() {
  echo -e "${YELLOW}=== DEBUG THÔNG TIN HỆ THỐNG ===${NC}"
  echo "Android:     $(getprop ro.build.version.release 2>/dev/null || echo 'Unknown')"
  echo "Model:       $(getprop ro.product.model 2>/dev/null || echo 'Unknown')"
  echo "Arch:        $(uname -m)"
  echo "Termux:      ${TERMUX_VERSION:-Unknown}"
  echo "Shell:       $SHELL"
  echo ""
  echo "Root runners:"
  command -v sudo >/dev/null 2>&1 && echo "  ✅ sudo" || echo "  ❌ sudo"
  command -v tsu  >/dev/null 2>&1 && echo "  ✅ tsu"  || echo "  ❌ tsu"
  command -v su   >/dev/null 2>&1 && echo "  ✅ su"   || echo "  ❌ su"
  echo ""
  echo "Công cụ mạng:"
  command -v iw >/dev/null 2>&1 && echo "  ✅ iw" || echo "  ❌ iw"
  command -v ip >/dev/null 2>&1 && echo "  ✅ ip" || echo "  ❌ ip"
  command -v wpa_supplicant >/dev/null 2>&1 && echo "  ✅ wpa_supplicant" || echo "  ❌ wpa_supplicant"
  echo ""
}

#####################################
# Parse tham số
#####################################
while (( "$#" )); do
  case "$1" in
    -d|--debug) DEBUG=true; shift;;
    -i|--iface) IFACE="${2:-}"; shift 2;;
    --branch)   BRANCH="${2:-}"; shift 2;;
    --no-py)    INSTALL_PY=false; shift;;
    --no-psutil)INSTALL_PSUTIL=false; shift;;
    --no-run)   RUN_AFTER_INSTALL=false; shift;;
    -h|--help)  usage; exit 0;;
    *) err "Tham số không hợp lệ: $1"; usage; exit 1;;
  esac
done

#####################################
# Cập nhật & cài package
#####################################
update_and_install() {
  info "Cập nhật gói của Termux..."
  yes | pkg update >/dev/null 2>&1 || true
  yes | pkg upgrade >/dev/null 2>&1 || true

  local base_pkgs=(root-repo git tsu python openssl libffi libcrypt clang make pkg-config unzip wget curl iproute2)
  local net_pkgs=(wpa-supplicant pixiewps iw)
  local all_pkgs=("${base_pkgs[@]}" "${net_pkgs[@]}")

  info "Cài packages cần thiết..."
  if ! pkg install -y "${all_pkgs[@]}" >/dev/null 2>&1; then
    warn "Cài hàng loạt thất bại, sẽ cài lần lượt:"
    for p in "${all_pkgs[@]}"; do
      if pkg install -y "$p" >/dev/null 2>&1; then
        echo "  ✅ $p"
      else
        echo "  ❌ $p (bỏ qua nếu không cần)"
      fi
    done
  else
    ok "Cài packages hoàn tất"
  fi
}

#####################################
# Cài Python packages
#####################################
install_python_deps() {
  if ! $INSTALL_PY; then
    warn "Bỏ qua cài Python packages (--no-py)."
    return 0
  fi

  info "Nâng cấp pip / setuptools / wheel..."
  python -m pip install --upgrade pip setuptools wheel >/dev/null 2>&1 || true

  info "Cài pycryptodome..."
  if python -m pip install --no-cache-dir pycryptodome >/dev/null 2>&1; then
    ok "pycryptodome OK"
  else
    warn "pycryptodome bản mới lỗi, thử phiên bản cố định..."
    python -m pip install pycryptodome==3.15.0 >/dev/null 2>&1 || warn "Không cài được pycryptodome"
  fi

  if $INSTALL_PSUTIL; then
    info "Cài psutil..."
    export CC=clang
    export CXX=clang++
    export CFLAGS="-I$PREFIX/include"
    export CXXFLAGS="-I$PREFIX/include"
    export LDFLAGS="-L$PREFIX/lib"
    if python -m pip install --only-binary=:all: psutil >/dev/null 2>&1; then
      ok "psutil (wheel) OK"
    elif python -m pip install --no-cache-dir psutil >/dev/null 2>&1; then
      ok "psutil (build) OK"
    else
      warn "Không cài được psutil. Tiếp tục không có psutil."
    fi
  else
    warn "Bỏ qua psutil (--no-psutil)."
  fi
}

#####################################
# Clone/Update repo
#####################################
sync_repo() {
  if [ ! -d "$REPO_DIR/.git" ]; then
    info "Clone repository $REPO_URL ..."
    if git clone --branch "$BRANCH" --depth 1 "$REPO_URL" "$REPO_DIR" >/dev/null 2>&1; then
      ok "Clone thành công"
    else
      err "Clone qua git thất bại. Thử tải ZIP..."
      local zipfile="${REPO_DIR}.zip"
      if command -v wget >/dev/null 2>&1; then
        wget -q "https://github.com/lilknighthood/thoitiet/archive/${BRANCH}.zip" -O "$zipfile"
      else
        curl -sL "https://github.com/lilknighthood/thoitiet/archive/${BRANCH}.zip" -o "$zipfile"
      fi
      unzip -q "$zipfile"
      rm -f "$zipfile"
      mv "thoitiet-${BRANCH}" "$REPO_DIR"
      ok "Tải ZIP & giải nén thành công"
    fi
  else
    info "Repo đã tồn tại, cập nhật nhánh $BRANCH..."
    pushd "$REPO_DIR" >/dev/null
      git fetch origin "$BRANCH" >/dev/null 2>&1 || true
      git checkout "$BRANCH" >/dev/null 2>&1 || true
      git pull --rebase origin "$BRANCH" >/dev/null 2>&1 || true
    popd >/dev/null
    ok "Repo được đồng bộ"
  fi
}

#####################################
# Chạy tool sau khi cài (ưu tiên sudo)
#####################################
run_tool() {
  if ! $RUN_AFTER_INSTALL; then
    warn "Bỏ qua chạy tool (--no-run). Bạn tự chạy sau:"
    echo -e "  ${YELLOW}cd ${REPO_DIR}${NC}"
    echo -e "  ${YELLOW}sudo python thoitietv2.py -i ${IFACE} -K${NC}"
    return 0
  fi

  if [ ! -f "${REPO_DIR}/thoitietv2.py" ]; then
    warn "Không tìm thấy thoitietv2.py trong repo. Bỏ qua chạy tự động."
    return 0
  fi

  pushd "$REPO_DIR" >/dev/null

  info "Thử chạy bằng sudo (ưu tiên theo yêu cầu)..."
  if command -v sudo >/dev/null 2>&1; then
    if sudo python thoitietv2.py -i "${IFACE}" -K; then
      ok "Chạy bằng sudo thành công."
      popd >/dev/null
      return 0
    else
      warn "Chạy bằng sudo thất bại. Thử phương án khác..."
    fi
  else
    warn "Không có sudo trong Termux. Sẽ thử tsu / su."
  fi

  info "Thử chạy bằng tsu -- ..."
  if command -v tsu >/dev/null 2>&1; then
    if tsu -- python thoitietv2.py -i "${IFACE}" -K; then
      ok "Chạy bằng tsu thành công."
      popd >/dev/null
      return 0
    else
      warn "Chạy bằng tsu thất bại."
    fi
  fi

  info "Thử chạy bằng su -c ..."
  if command -v su >/dev/null 2>&1; then
    # dùng sh -lc để đảm bảo PATH & cwd
    if su -c "sh -lc 'cd $(pwd) && python thoitietv2.py -i ${IFACE} -K'"; then
      ok "Chạy bằng su -c thành công."
      popd >/dev/null
      return 0
    else
      warn "Chạy bằng su -c thất bại."
    fi
  fi

  warn "Không có sudo/tsu/su hoặc tất cả đều lỗi. Thử chạy không root (có thể thiếu quyền)..."
  python thoitietv2.py -i "${IFACE}" -K || warn "Chạy thường cũng thất bại."

  popd >/dev/null
}

#####################################
# MAIN
#####################################
echo -e "${GREEN}=== Bắt đầu cài đặt WiFi Tool cho Termux ===${NC}"
$DEBUG && debug_system
update_and_install
install_python_deps
sync_repo
run_tool
ok "Hoàn tất!"
echo ""
echo -e "${CYAN}Lần sau sử dụng:${NC}"
echo -e "  ${YELLOW}cd ${REPO_DIR}${NC}"
echo -e "  ${YELLOW}sudo python thoitietv2.py -i ${IFACE} -K${NC}"
