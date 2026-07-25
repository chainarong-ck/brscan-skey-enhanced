#!/bin/bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PREFIX="${PREFIX:-/usr/local}"
DESTDIR="${DESTDIR:-}"
SETUP_USER=""
SKIP_USER_SETUP=false

usage() {
    cat <<'EOF'
Usage: ./install.sh [OPTIONS]

Install brscan-skey-enhanced for all users.

Options:
  --prefix PATH       Installation prefix (default: /usr/local)
  --destdir PATH      Staging root for package creation
  --user USER         Initialize ~/.brscan-skey for USER after installation
  --no-user-setup     Do not initialize a user's files
  -h, --help          Show this help
EOF
}

while [ "$#" -gt 0 ]; do
    case "$1" in
        --prefix)
            [ "$#" -ge 2 ] || {
                echo "install.sh: --prefix requires a path" >&2
                exit 2
            }
            PREFIX="$2"
            shift 2
            ;;
        --destdir)
            [ "$#" -ge 2 ] || {
                echo "install.sh: --destdir requires a path" >&2
                exit 2
            }
            DESTDIR="$2"
            shift 2
            ;;
        --user)
            [ "$#" -ge 2 ] || {
                echo "install.sh: --user requires a user name" >&2
                exit 2
            }
            SETUP_USER="$2"
            shift 2
            ;;
        --no-user-setup)
            SKIP_USER_SETUP=true
            shift
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

case "$PREFIX" in
    /*) ;;
    *)
        echo "install.sh: --prefix must be an absolute path" >&2
        exit 2
        ;;
esac
if [ -n "$DESTDIR" ]; then
    case "$DESTDIR" in
        /*) ;;
        *)
            echo "install.sh: --destdir must be an absolute path" >&2
            exit 2
            ;;
    esac
fi

if [ -z "$DESTDIR" ] && [ "$(id -u)" -ne 0 ]; then
    case "$PREFIX" in
        /usr|/usr/*|/opt|/opt/*)
            echo "System-wide installation requires root." >&2
            echo "Run: sudo ./install.sh" >&2
            exit 1
            ;;
    esac
fi

INSTALL_PREFIX="${DESTDIR%/}${PREFIX}"
APP_DIR="$INSTALL_PREFIX/lib/brscan-skey-enhanced"
BIN_DIR="$INSTALL_PREFIX/bin"
APPLICATIONS_DIR="$INSTALL_PREFIX/share/applications"

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
for file in "$PROJECT_DIR"/bin/*; do
    install -m 0755 "$file" "$BIN_DIR/"
done
install -m 0644 \
    "$PROJECT_DIR/packaging/brscan-skey-config.desktop" \
    "$APPLICATIONS_DIR/brscan-skey-config.desktop"

echo "Installed application files under $INSTALL_PREFIX"

if [ -n "$DESTDIR" ] || [ "$SKIP_USER_SETUP" = true ]; then
    if [ -n "$DESTDIR" ]; then
        echo "Staging install complete; per-user setup was skipped."
    fi
    exit 0
fi

if [ -z "$SETUP_USER" ]; then
    if [ -n "${SUDO_USER:-}" ] && [ "$SUDO_USER" != root ]; then
        SETUP_USER="$SUDO_USER"
    elif [ "$(id -u)" -ne 0 ]; then
        SETUP_USER="$(id -un)"
    fi
fi

if [ -z "$SETUP_USER" ]; then
    echo "No regular user was selected."
    echo "Each user can initialize their files with: brscan-skey-setup-user"
    exit 0
fi

if ! id "$SETUP_USER" >/dev/null 2>&1; then
    echo "install.sh: user does not exist: $SETUP_USER" >&2
    exit 1
fi

USER_HOME="$(getent passwd "$SETUP_USER" | cut -d: -f6)"
if [ -z "$USER_HOME" ]; then
    echo "install.sh: cannot determine home directory for $SETUP_USER" >&2
    exit 1
fi

SETUP_COMMAND="$PREFIX/bin/brscan-skey-setup-user"
if [ "$SETUP_USER" = "$(id -un)" ]; then
    HOME="$USER_HOME" \
        BRSCAN_SKEY_HOME="$USER_HOME/.brscan-skey" \
        "$SETUP_COMMAND"
elif [ "$(id -u)" -eq 0 ] && command -v runuser >/dev/null 2>&1; then
    runuser -u "$SETUP_USER" -- env \
        HOME="$USER_HOME" \
        BRSCAN_SKEY_HOME="$USER_HOME/.brscan-skey" \
        "$SETUP_COMMAND"
else
    echo "Application installed, but user setup could not be run as $SETUP_USER." >&2
    echo "Log in as that user and run: brscan-skey-setup-user" >&2
    exit 1
fi
