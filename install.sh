#!/bin/bash
set -euo pipefail

SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ORIGINAL_ARGS=("$@")
PREFIX="${BRSCAN_INSTALL_PREFIX:-/usr/local}"
INSTALL_DEPS=1
CHECK_DRIVER=1
INTEGRATE_ONLY=0

usage() {
    cat <<'EOF'
วิธีใช้: ./install.sh [ตัวเลือก]

ตัวเลือก:
  --no-deps             ไม่ติดตั้ง dependencies อัตโนมัติ
  --skip-driver-check   ติดตั้งต่อแม้ยังไม่พบ Brother brscan-skey
  --integrate-only      เชื่อมปุ่มสแกนอีกครั้งโดยไม่ติดตั้งไฟล์โปรแกรม
  -h, --help            แสดงข้อความนี้
EOF
}

while [ "$#" -gt 0 ]; do
    case "$1" in
        --no-deps)
            INSTALL_DEPS=0
            ;;
        --skip-driver-check)
            CHECK_DRIVER=0
            ;;
        --integrate-only)
            INTEGRATE_ONLY=1
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "ไม่รู้จักตัวเลือก: $1" >&2
            usage >&2
            exit 2
            ;;
    esac
    shift
done

if [ "${EUID:-$(id -u)}" -ne 0 ] &&
    [ "${BRSCAN_ALLOW_UNPRIVILEGED_TESTS:-0}" != "1" ]
then
    if ! command -v sudo >/dev/null 2>&1; then
        echo "ต้องใช้สิทธิ์ผู้ดูแลระบบ แต่ไม่พบคำสั่ง sudo" >&2
        exit 1
    fi
    exec sudo -- "$0" "${ORIGINAL_ARGS[@]}"
fi

BROTHER_SCRIPT_DIR="${BRSCAN_BROTHER_SCRIPT_DIR:-/opt/brother/scanner/brscan-skey/script}"
if [ "$CHECK_DRIVER" -eq 1 ] && [ ! -d "$BROTHER_SCRIPT_DIR" ]; then
    cat >&2 <<'EOF'
ยังไม่พบ Brother brscan-skey

กรุณาติดตั้ง Scanner Driver และ Scanner Setting file (brscan-skey)
สำหรับเครื่องสแกนรุ่นที่ใช้งานจาก https://support.brother.com/ ก่อน
จากนั้นจึงรันตัวติดตั้งนี้อีกครั้ง
EOF
    exit 2
fi

install_dependencies() {
    local needs_install=0
    command -v python3 >/dev/null 2>&1 || needs_install=1
    if ! command -v magick >/dev/null 2>&1 &&
        ! command -v convert >/dev/null 2>&1
    then
        needs_install=1
    fi
    if ! python3 -c \
        'import gi; gi.require_version("Gtk", "3.0"); from gi.repository import Gtk' \
        >/dev/null 2>&1
    then
        needs_install=1
    fi
    [ "$needs_install" -eq 1 ] || return 0

    if command -v apt-get >/dev/null 2>&1; then
        apt-get update
        DEBIAN_FRONTEND=noninteractive apt-get install -y \
            python3 python3-gi gir1.2-gtk-3.0 imagemagick xdg-utils
    elif command -v dnf >/dev/null 2>&1; then
        dnf install -y \
            python3 python3-gobject gtk3 ImageMagick xdg-utils
    else
        echo "ไม่รองรับ package manager ของระบบนี้" >&2
        echo "กรุณาติดตั้ง Python 3, GTK 3/PyGObject และ ImageMagick เอง" >&2
        return 1
    fi
}

if [ "$INSTALL_DEPS" -eq 1 ] && [ "$INTEGRATE_ONLY" -eq 0 ]; then
    echo "ตรวจสอบ dependencies..."
    install_dependencies
fi

LIB_DIR="$PREFIX/lib/brscan-skey-enhanced"
SHARE_DIR="$PREFIX/share/brscan-skey-enhanced"

if [ "$INTEGRATE_ONLY" -eq 0 ]; then
    echo "ติดตั้งไฟล์โปรแกรม..."
    install -d \
        "$LIB_DIR/configurator" \
        "$LIB_DIR/script" \
        "$SHARE_DIR/brother-config" \
        "$PREFIX/bin" \
        "$PREFIX/share/applications" \
        "$PREFIX/share/icons/hicolor/scalable/apps"

    install -m 0644 "$SOURCE_DIR"/configurator/*.py "$LIB_DIR/configurator/"
    install -m 0755 "$SOURCE_DIR"/script/*.sh "$LIB_DIR/script/"
    install -m 0644 "$SOURCE_DIR"/*.config "$SHARE_DIR/brother-config/"
    install -m 0755 "$SOURCE_DIR"/bin/* "$PREFIX/bin/"
    install -m 0644 \
        "$SOURCE_DIR/assets/brscan-skey-enhanced.desktop" \
        "$PREFIX/share/applications/"
    install -m 0644 \
        "$SOURCE_DIR/assets/brscan-skey-enhanced.svg" \
        "$PREFIX/share/icons/hicolor/scalable/apps/"
fi

echo "เชื่อมปุ่มสแกน..."
if [ -d "$BROTHER_SCRIPT_DIR" ]; then
    BRSCAN_SHARE_DIR="$SHARE_DIR" \
    BRSCAN_BROTHER_SCRIPT_DIR="$BROTHER_SCRIPT_DIR" \
        "$PREFIX/bin/brscan-skey-enhanced-integrate" install
else
    echo "ยังไม่ได้เชื่อมปุ่มสแกน เพราะไม่พบ Brother brscan-skey" >&2
    echo "หลังติดตั้งไดรเวอร์แล้ว ให้รัน: sudo $0 --integrate-only" >&2
fi

if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$PREFIX/share/applications" || true
fi
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -q "$PREFIX/share/icons/hicolor" || true
fi

cat <<'EOF'

ติดตั้งเรียบร้อยแล้ว

เปิด “Brother Scan Settings” จากเมนูแอปพลิเคชัน หรือใช้คำสั่ง:
  brscan-skey-settings

ตรวจสอบระบบด้วยคำสั่ง:
  brscan-skey-enhanced-check
EOF
