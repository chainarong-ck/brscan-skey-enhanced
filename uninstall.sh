#!/bin/bash
set -euo pipefail

PREFIX="${PREFIX:-/usr/local}"
DESTDIR="${DESTDIR:-}"

usage() {
    cat <<'EOF'
Usage: ./uninstall.sh [OPTIONS]

Remove the system-wide brscan-skey-enhanced application.
Per-user ~/.brscan-skey files are always preserved.

Options:
  --prefix PATH       Installation prefix (default: /usr/local)
  --destdir PATH      Staging root used during installation
  -h, --help          Show this help
EOF
}

while [ "$#" -gt 0 ]; do
    case "$1" in
        --prefix)
            [ "$#" -ge 2 ] || {
                echo "uninstall.sh: --prefix requires a path" >&2
                exit 2
            }
            PREFIX="$2"
            shift 2
            ;;
        --destdir)
            [ "$#" -ge 2 ] || {
                echo "uninstall.sh: --destdir requires a path" >&2
                exit 2
            }
            DESTDIR="$2"
            shift 2
            ;;
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

case "$PREFIX" in
    /*) ;;
    *)
        echo "uninstall.sh: PREFIX must be an absolute path" >&2
        exit 2
        ;;
esac
if [ -n "$DESTDIR" ]; then
    case "$DESTDIR" in
        /*) ;;
        *)
            echo "uninstall.sh: DESTDIR must be an absolute path" >&2
            exit 2
            ;;
    esac
fi

if [ -z "$DESTDIR" ] && [ "$(id -u)" -ne 0 ]; then
    case "$PREFIX" in
        /usr|/usr/*|/opt|/opt/*)
            echo "System-wide removal requires root." >&2
            echo "Run: sudo ./uninstall.sh" >&2
            exit 1
            ;;
    esac
fi

INSTALL_PREFIX="${DESTDIR%/}${PREFIX}"
APP_DIR="$INSTALL_PREFIX/lib/brscan-skey-enhanced"

rm -f \
    "$INSTALL_PREFIX/bin/brscan-skey-config" \
    "$INSTALL_PREFIX/bin/brscan-skey-read-settings" \
    "$INSTALL_PREFIX/bin/brscan-skey-setup-user" \
    "$INSTALL_PREFIX/share/applications/brscan-skey-config.desktop"
rm -rf -- "$APP_DIR"

echo "Removed the system-wide brscan-skey-enhanced application."
echo "Per-user ~/.brscan-skey files were preserved and can be removed manually."
