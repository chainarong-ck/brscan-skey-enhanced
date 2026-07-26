#!/bin/bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_PREFIX=/usr/local
APP_DIR="$INSTALL_PREFIX/lib/brscan-skey-enhanced"
BIN_DIR="$INSTALL_PREFIX/bin"
APPLICATIONS_DIR="$INSTALL_PREFIX/share/applications"
GUI_DEFAULT=""

usage() {
    cat <<'EOF'
Usage: sudo ./install.sh [--gui gtk|qt]

Install brscan-skey-enhanced system-wide under /usr/local.

Options:
  --gui gtk|qt        Default GUI for menu and option-free launches
  -h, --help          Show this help
EOF
}

while [ "$#" -gt 0 ]; do
    case "$1" in
        --gui)
            [ "$#" -ge 2 ] || {
                echo "install.sh: --gui requires gtk or qt" >&2
                exit 2
            }
            GUI_DEFAULT="${2,,}"
            shift 2
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "install.sh: unknown option: $1" >&2
            usage >&2
            exit 2
            ;;
    esac
done

case "$GUI_DEFAULT" in
    ""|gtk|qt) ;;
    *)
        echo "install.sh: --gui must be gtk or qt" >&2
        exit 2
        ;;
esac

if [ "$(id -u)" -ne 0 ]; then
    echo "System-wide installation requires root." >&2
    echo "Run: sudo ./install.sh" >&2
    exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
    echo "Python 3 is required." >&2
    exit 1
fi
if ! python3 -c 'import sys; raise SystemExit(sys.version_info < (3, 9))'
then
    echo "Python 3.9 or newer is required." >&2
    exit 1
fi

if [ -z "$GUI_DEFAULT" ]; then
    echo
    echo "Choose the default GUI for Brother Scan Settings:"
    echo "  1) GTK 3 (recommended)"
    echo "  2) Qt 6"
    printf "Selection [1]: "
    if ! IFS= read -r GUI_CHOICE; then
        GUI_CHOICE=""
    fi
    GUI_CHOICE="${GUI_CHOICE:-1}"
    GUI_CHOICE="${GUI_CHOICE,,}"
    case "$GUI_CHOICE" in
        1|gtk) GUI_DEFAULT=gtk ;;
        2|qt) GUI_DEFAULT=qt ;;
        *)
            echo "install.sh: select 1 for GTK or 2 for Qt" >&2
            exit 2
            ;;
    esac
fi

case "$GUI_DEFAULT" in
    gtk)
        if ! python3 -c \
            'import gi; gi.require_version("Gtk", "3.0"); from gi.repository import Gtk'
        then
            echo "GTK 3 with PyGObject is required for --gui gtk." >&2
            exit 1
        fi
        ;;
    qt)
        if ! python3 -c '
import importlib
import importlib.util

module = (
    "PySide6.QtWidgets"
    if importlib.util.find_spec("PySide6")
    else "PyQt6.QtWidgets"
)
importlib.import_module(module)
'
        then
            echo "PySide6 or PyQt6 is required for --gui qt." >&2
            exit 1
        fi
        ;;
esac

if ! command -v magick >/dev/null 2>&1; then
    echo "Warning: ImageMagick 'magick' was not found." >&2
fi
if [ ! -x /opt/brother/scanner/brscan-skey/skey-scanimage ]; then
    echo "Warning: Brother skey-scanimage was not found." >&2
fi

# Recreate only the application-owned tree so removed files cannot linger.
rm -rf -- "$APP_DIR"
install -d -m 0755 \
    "$APP_DIR/configurator" \
    "$APP_DIR/script" \
    "$BIN_DIR" \
    "$APPLICATIONS_DIR"

for file in "$PROJECT_DIR"/configurator/*.py; do
    install -m 0644 "$file" "$APP_DIR/configurator/"
done
for file in \
    scantofile.config \
    scantoemail.config \
    scantoimage.config
do
    install -m 0644 "$PROJECT_DIR/$file" "$APP_DIR/$file"
done
for file in "$PROJECT_DIR"/script/*.sh; do
    install -m 0755 "$file" "$APP_DIR/script/"
done
install -m 0755 \
    "$PROJECT_DIR/bin/brscan-skey-config" \
    "$BIN_DIR/brscan-skey-config"
install -m 0755 \
    "$PROJECT_DIR/bin/brscan-skey-read-settings" \
    "$BIN_DIR/brscan-skey-read-settings"
install -m 0644 \
    "$PROJECT_DIR/packaging/brscan-skey-config.desktop" \
    "$APPLICATIONS_DIR/brscan-skey-config.desktop"
printf '%s\n' "$GUI_DEFAULT" |
    install -m 0644 /dev/stdin "$APP_DIR/default-gui"

echo
echo "Installed brscan-skey-enhanced under $INSTALL_PREFIX"
echo "Default GUI: $GUI_DEFAULT"
echo "Per-user files will be created when each user first opens:"
echo "  brscan-skey-config"
