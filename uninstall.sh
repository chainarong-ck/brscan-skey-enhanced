#!/bin/bash
set -euo pipefail

PREFIX="${BRSCAN_INSTALL_PREFIX:-/usr/local}"
LIB_DIR="$PREFIX/lib/brscan-skey-enhanced"
SHARE_DIR="$PREFIX/share/brscan-skey-enhanced"
BROTHER_SCRIPT_DIR="${BRSCAN_BROTHER_SCRIPT_DIR:-/opt/brother/scanner/brscan-skey/script}"

if [ "${EUID:-$(id -u)}" -ne 0 ] &&
    [ "${BRSCAN_ALLOW_UNPRIVILEGED_TESTS:-0}" != "1" ]
then
    if ! command -v sudo >/dev/null 2>&1; then
        echo "ต้องใช้สิทธิ์ผู้ดูแลระบบ แต่ไม่พบคำสั่ง sudo" >&2
        exit 1
    fi
    exec sudo -- "$0"
fi

if [ -x "$PREFIX/bin/brscan-skey-enhanced-integrate" ]; then
    BRSCAN_SHARE_DIR="$SHARE_DIR" \
    BRSCAN_BROTHER_SCRIPT_DIR="$BROTHER_SCRIPT_DIR" \
        "$PREFIX/bin/brscan-skey-enhanced-integrate" remove
fi

rm -f -- \
    "$PREFIX/bin/brscan-skey-settings" \
    "$PREFIX/bin/brscan-skey-enhanced-check" \
    "$PREFIX/bin/brscan-skey-enhanced-integrate" \
    "$PREFIX/share/applications/brscan-skey-enhanced.desktop" \
    "$PREFIX/share/icons/hicolor/scalable/apps/brscan-skey-enhanced.svg"
rm -rf -- "$LIB_DIR" "$SHARE_DIR"

if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$PREFIX/share/applications" || true
fi
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -q "$PREFIX/share/icons/hicolor" || true
fi

cat <<'EOF'
ถอนการติดตั้งเรียบร้อยแล้ว
คืนค่า configuration เดิมของ Brother แล้ว (หากมีไฟล์สำรอง)
ค่าของผู้ใช้ใน ~/.config/brscan-skey-enhanced/ ยังถูกเก็บไว้
EOF
