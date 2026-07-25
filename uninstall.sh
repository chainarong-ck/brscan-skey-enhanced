#!/bin/bash
set -euo pipefail

INSTALL_PREFIX=/usr/local
APP_DIR="$INSTALL_PREFIX/lib/brscan-skey-enhanced"

usage() {
    cat <<'EOF'
Usage: sudo ./uninstall.sh

Remove the system-wide brscan-skey-enhanced application.
Per-user ~/.brscan-skey files are preserved.
EOF
}

while [ "$#" -gt 0 ]; do
    case "$1" in
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "uninstall.sh: unknown option: $1" >&2
            usage >&2
            exit 2
            ;;
    esac
done

if [ "$(id -u)" -ne 0 ]; then
    echo "System-wide removal requires root." >&2
    echo "Run: sudo ./uninstall.sh" >&2
    exit 1
fi

rm -f \
    "$INSTALL_PREFIX/bin/brscan-skey-config" \
    "$INSTALL_PREFIX/bin/brscan-skey-read-settings" \
    "$INSTALL_PREFIX/bin/brscan-skey-setup-user" \
    "$INSTALL_PREFIX/share/applications/brscan-skey-config.desktop"
rm -rf -- "$APP_DIR"

echo "Removed the system-wide brscan-skey-enhanced application."
echo "Per-user ~/.brscan-skey files were preserved."
