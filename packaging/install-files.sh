#!/bin/bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [ "$#" -lt 1 ] || [ "$#" -gt 3 ]; then
    echo "Usage: install-files.sh DESTDIR [PREFIX] [gtk|qt]" >&2
    exit 2
fi

DESTDIR="${1%/}"
INSTALL_PREFIX="${2:-/usr}"
DEFAULT_GUI="${3:-gtk}"

case "$DESTDIR" in
    /*) ;;
    *)
        echo "install-files.sh: DESTDIR must be an absolute path" >&2
        exit 2
        ;;
esac
case "$INSTALL_PREFIX" in
    /*) ;;
    *)
        echo "install-files.sh: PREFIX must be an absolute path" >&2
        exit 2
        ;;
esac
case "$DEFAULT_GUI" in
    gtk|qt) ;;
    *)
        echo "install-files.sh: default GUI must be gtk or qt" >&2
        exit 2
        ;;
esac

APP_DIR="$DESTDIR$INSTALL_PREFIX/lib/brscan-skey-enhanced"
BIN_DIR="$DESTDIR$INSTALL_PREFIX/bin"
APPLICATIONS_DIR="$DESTDIR$INSTALL_PREFIX/share/applications"
DOC_DIR="$DESTDIR$INSTALL_PREFIX/share/doc/brscan-skey-enhanced"

install -d -m 0755 \
    "$APP_DIR/configurator" \
    "$APP_DIR/script" \
    "$BIN_DIR" \
    "$APPLICATIONS_DIR" \
    "$DOC_DIR"

for file in "$PROJECT_DIR"/configurator/*.py; do
    [ -e "$file" ] || continue
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
    [ -e "$file" ] || continue
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
install -m 0644 "$PROJECT_DIR/README.md" "$DOC_DIR/README.md"
install -m 0644 "$PROJECT_DIR/VERSION" "$DOC_DIR/VERSION"
install -m 0644 "$PROJECT_DIR/LICENSE" "$DOC_DIR/LICENSE"
install -m 0644 "$PROJECT_DIR/packaging/copyright" "$DOC_DIR/copyright"
printf '%s\n' "$DEFAULT_GUI" |
    install -m 0644 /dev/stdin "$APP_DIR/default-gui"
