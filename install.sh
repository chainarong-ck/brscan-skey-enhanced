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

if [ -z "$GUI_DEFAULT" ]; then
    CURRENT_GUI=""
    if [ -f "$APP_DIR/default-gui" ]; then
        IFS= read -r CURRENT_GUI < "$APP_DIR/default-gui" || true
        case "$CURRENT_GUI" in
            gtk|qt) ;;
            *) CURRENT_GUI="" ;;
        esac
    fi

    echo
    echo "Choose the default GUI for Brother Scan Settings:"
    echo "  1) GTK 3 (recommended)"
    echo "  2) Qt 6"
    if [ "$CURRENT_GUI" = qt ]; then
        DEFAULT_CHOICE=2
    else
        DEFAULT_CHOICE=1
    fi
    printf "Selection [%s]: " "$DEFAULT_CHOICE"
    if ! IFS= read -r GUI_CHOICE; then
        GUI_CHOICE=""
    fi
    GUI_CHOICE="${GUI_CHOICE:-$DEFAULT_CHOICE}"
    case "$GUI_CHOICE" in
        1|gtk|GTK) GUI_DEFAULT=gtk ;;
        2|qt|QT) GUI_DEFAULT=qt ;;
        *)
            echo "install.sh: select 1 for GTK or 2 for Qt" >&2
            exit 2
            ;;
    esac
fi

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
    scantoimage.config \
    settings.ini.example
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
# Remove the launcher used by older releases; setup now happens on first launch.
rm -f "$BIN_DIR/brscan-skey-setup-user"
install -m 0644 \
    "$PROJECT_DIR/packaging/brscan-skey-config.desktop" \
    "$APPLICATIONS_DIR/brscan-skey-config.desktop"
install -m 0644 \
    "$PROJECT_DIR/packaging/default-gui.$GUI_DEFAULT" \
    "$APP_DIR/default-gui"

echo
echo "Installed brscan-skey-enhanced under $INSTALL_PREFIX"
echo "Default GUI: $GUI_DEFAULT"
echo "Per-user files will be created when each user first opens:"
echo "  brscan-skey-config"
