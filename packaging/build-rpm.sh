#!/bin/bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUTPUT_DIR="${1:-$PROJECT_DIR/dist}"
PACKAGE_NAME=brscan-skey-enhanced

for command_name in rpmbuild tar; do
    if ! command -v "$command_name" >/dev/null 2>&1; then
        echo "build-rpm.sh: $command_name is required" >&2
        exit 1
    fi
done

VERSION="$(tr -d '[:space:]' < "$PROJECT_DIR/VERSION")"
if [[ ! "$VERSION" =~ ^[0-9]+([.][0-9]+)*$ ]]; then
    echo "build-rpm.sh: invalid version in VERSION: $VERSION" >&2
    exit 1
fi

mkdir -p "$OUTPUT_DIR"
OUTPUT_DIR="$(cd "$OUTPUT_DIR" && pwd)"
BUILD_DIR="$(mktemp -d)"
trap 'rm -rf -- "$BUILD_DIR"' EXIT

RPM_ROOT="$BUILD_DIR/rpmbuild"
install -d -m 0755 \
    "$RPM_ROOT/BUILD" \
    "$RPM_ROOT/BUILDROOT" \
    "$RPM_ROOT/RPMS" \
    "$RPM_ROOT/SOURCES" \
    "$RPM_ROOT/SPECS" \
    "$RPM_ROOT/SRPMS" \
    "$RPM_ROOT/TMP"

tar \
    --exclude='*/__pycache__' \
    --exclude='*.py[co]' \
    --transform "s,^,$PACKAGE_NAME-$VERSION/," \
    -C "$PROJECT_DIR" \
    -czf "$RPM_ROOT/SOURCES/$PACKAGE_NAME-$VERSION.tar.gz" \
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

rpmbuild \
    --define "_topdir $RPM_ROOT" \
    --define "_tmppath $RPM_ROOT/TMP" \
    --define "package_version $VERSION" \
    -ba "$PROJECT_DIR/packaging/brscan-skey-enhanced.spec"

find "$RPM_ROOT/RPMS" "$RPM_ROOT/SRPMS" \
    -type f -name '*.rpm' \
    -exec install -m 0644 {} "$OUTPUT_DIR/" \;
echo "Built RPM packages in $OUTPUT_DIR"
