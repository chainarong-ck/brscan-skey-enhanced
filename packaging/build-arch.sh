#!/bin/bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUTPUT_DIR="${1:-$PROJECT_DIR/dist}"
PACKAGE_NAME=brscan-skey-enhanced
PKGBUILD_SOURCE="$PROJECT_DIR/packaging/arch/PKGBUILD"

for command_name in makepkg sha256sum tar; do
    if ! command -v "$command_name" >/dev/null 2>&1; then
        echo "build-arch.sh: $command_name is required" >&2
        exit 1
    fi
done

VERSION="$(tr -d '[:space:]' < "$PROJECT_DIR/VERSION")"
if [[ ! "$VERSION" =~ ^[0-9]+([.][0-9]+)*$ ]]; then
    echo "build-arch.sh: invalid version in VERSION: $VERSION" >&2
    exit 1
fi

PKGBUILD_VERSION="$(
    bash -c 'source "$1"; printf "%s" "$pkgver"' bash "$PKGBUILD_SOURCE"
)"
if [ "$PKGBUILD_VERSION" != "$VERSION" ]; then
    echo "build-arch.sh: VERSION and PKGBUILD pkgver do not match" >&2
    echo "VERSION=$VERSION PKGBUILD=$PKGBUILD_VERSION" >&2
    exit 1
fi

mkdir -p "$OUTPUT_DIR"
OUTPUT_DIR="$(cd "$OUTPUT_DIR" && pwd)"
BUILD_DIR="$(mktemp -d)"
trap 'rm -rf -- "$BUILD_DIR"' EXIT

SOURCE_ARCHIVE="$BUILD_DIR/$PACKAGE_NAME-$VERSION.tar.gz"
tar \
    --exclude='*/__pycache__' \
    --exclude='*.py[co]' \
    --transform "s,^,$PACKAGE_NAME-$VERSION/," \
    -C "$PROJECT_DIR" \
    -czf "$SOURCE_ARCHIVE" \
    LICENSE \
    README.md \
    VERSION \
    bin \
    configurator \
    install.sh \
    packaging \
    scantoemail.config \
    scantofile.config \
    scantoimage.config \
    script \
    tests \
    uninstall.sh

SOURCE_SHA256="$(sha256sum "$SOURCE_ARCHIVE")"
SOURCE_SHA256="${SOURCE_SHA256%% *}"
sed "s/sha256sums=('SKIP')/sha256sums=('$SOURCE_SHA256')/" \
    "$PKGBUILD_SOURCE" > "$BUILD_DIR/PKGBUILD"
if ! grep -Fq "sha256sums=('$SOURCE_SHA256')" "$BUILD_DIR/PKGBUILD"; then
    echo "build-arch.sh: could not render source checksum" >&2
    exit 1
fi

(
    cd "$BUILD_DIR" || exit 1
    PKGDEST="$OUTPUT_DIR" makepkg --cleanbuild --force
)

echo "Built Arch Linux package in $OUTPUT_DIR"
