#!/bin/bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUTPUT_DIR="${1:-$PROJECT_DIR/dist}"
PACKAGE_NAME=brscan-skey-enhanced

if ! command -v dpkg-deb >/dev/null 2>&1; then
    echo "build-deb.sh: dpkg-deb is required" >&2
    exit 1
fi

VERSION="$(tr -d '[:space:]' < "$PROJECT_DIR/VERSION")"
if [[ ! "$VERSION" =~ ^[0-9]+([.][0-9]+)*$ ]]; then
    echo "build-deb.sh: invalid version in VERSION: $VERSION" >&2
    exit 1
fi
PACKAGE_VERSION="$VERSION-1"

mkdir -p "$OUTPUT_DIR"
OUTPUT_DIR="$(cd "$OUTPUT_DIR" && pwd)"
BUILD_DIR="$(mktemp -d)"
trap 'rm -rf -- "$BUILD_DIR"' EXIT

PACKAGE_ROOT="$BUILD_DIR/${PACKAGE_NAME}_${PACKAGE_VERSION}_all"
"$PROJECT_DIR/packaging/install-files.sh" "$PACKAGE_ROOT" /usr gtk
install -d -m 0755 "$PACKAGE_ROOT/DEBIAN"
sed "s/@PACKAGE_VERSION@/$PACKAGE_VERSION/g" \
    "$PROJECT_DIR/packaging/debian/control" \
    > "$PACKAGE_ROOT/DEBIAN/control"
chmod 0644 "$PACKAGE_ROOT/DEBIAN/control"

(
    cd "$PACKAGE_ROOT"
    find usr -type f -print0 |
        sort -z |
        xargs -0 md5sum > DEBIAN/md5sums
)
chmod 0644 "$PACKAGE_ROOT/DEBIAN/md5sums"

PACKAGE_PATH="$OUTPUT_DIR/${PACKAGE_NAME}_${PACKAGE_VERSION}_all.deb"
dpkg-deb --root-owner-group --build "$PACKAGE_ROOT" "$PACKAGE_PATH"
echo "Built $PACKAGE_PATH"
