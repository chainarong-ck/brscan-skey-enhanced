#!/bin/bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VERSION="${VERSION_OVERRIDE:-$(<"$PROJECT_DIR/VERSION")}"
OUTPUT_DIR="${OUTPUT_DIR:-$PROJECT_DIR/dist}"
BUILD_DEB=1
BUILD_RPM=1

usage() {
    cat <<'EOF'
Usage: packaging/build-packages.sh [--deb-only|--rpm-only]

Environment:
  VERSION_OVERRIDE  Override the version from VERSION
  OUTPUT_DIR        Package output directory (default: dist)
EOF
}

case "${1:-}" in
    "")
        ;;
    --deb-only)
        BUILD_RPM=0
        ;;
    --rpm-only)
        BUILD_DEB=0
        ;;
    -h|--help)
        usage
        exit 0
        ;;
    *)
        usage >&2
        exit 2
        ;;
esac

if [[ ! "$VERSION" =~ ^[0-9]+([.][0-9]+)*([~-][0-9A-Za-z.+]+)?$ ]]; then
    echo "Invalid package version: $VERSION" >&2
    exit 2
fi

BUILD_TEMP="$(mktemp -d /tmp/brscan-skey-enhanced-build.XXXXXX)"
trap 'rm -rf -- "$BUILD_TEMP"' EXIT
mkdir -p "$OUTPUT_DIR"

install_payload() {
    local root="$1"
    install -d \
        "$root/usr/lib/brscan-skey-enhanced/configurator" \
        "$root/usr/lib/brscan-skey-enhanced/script" \
        "$root/usr/share/brscan-skey-enhanced/brother-config" \
        "$root/usr/bin" \
        "$root/usr/share/applications" \
        "$root/usr/share/icons/hicolor/scalable/apps"
    install -m 0644 "$PROJECT_DIR"/configurator/*.py \
        "$root/usr/lib/brscan-skey-enhanced/configurator/"
    install -m 0755 "$PROJECT_DIR"/script/*.sh \
        "$root/usr/lib/brscan-skey-enhanced/script/"
    install -m 0644 "$PROJECT_DIR"/*.config \
        "$root/usr/share/brscan-skey-enhanced/brother-config/"
    install -m 0755 "$PROJECT_DIR"/bin/* "$root/usr/bin/"
    install -m 0644 "$PROJECT_DIR/assets/brscan-skey-enhanced.desktop" \
        "$root/usr/share/applications/"
    install -m 0644 "$PROJECT_DIR/assets/brscan-skey-enhanced.svg" \
        "$root/usr/share/icons/hicolor/scalable/apps/"
}

build_deb() {
    if ! command -v dpkg-deb >/dev/null 2>&1; then
        echo "dpkg-deb is required to build the DEB package" >&2
        return 1
    fi

    local package_root="$BUILD_TEMP/deb"
    install_payload "$package_root"
    install -d "$package_root/DEBIAN"
    sed "s/@VERSION@/$VERSION/g" \
        "$PROJECT_DIR/packaging/debian/control.in" \
        >"$package_root/DEBIAN/control"
    install -m 0755 "$PROJECT_DIR/packaging/debian/postinst" \
        "$package_root/DEBIAN/postinst"
    install -m 0755 "$PROJECT_DIR/packaging/debian/prerm" \
        "$package_root/DEBIAN/prerm"

    dpkg-deb --build --root-owner-group "$package_root" \
        "$OUTPUT_DIR/brscan-skey-enhanced_${VERSION}_all.deb"
}

copy_rpm_source() {
    local source_root="$1"
    install -d "$source_root"
    cp -a \
        "$PROJECT_DIR/assets" \
        "$PROJECT_DIR/bin" \
        "$PROJECT_DIR/configurator" \
        "$PROJECT_DIR/script" \
        "$source_root/"
    install -m 0644 "$PROJECT_DIR"/*.config "$source_root/"
}

build_rpm() {
    if ! command -v rpmbuild >/dev/null 2>&1; then
        echo "rpmbuild is required to build the RPM package" >&2
        return 1
    fi

    local top_dir="$BUILD_TEMP/rpmbuild"
    local source_name="brscan-skey-enhanced-$VERSION"
    local source_root="$BUILD_TEMP/$source_name"
    install -d \
        "$top_dir/BUILD" \
        "$top_dir/BUILDROOT" \
        "$top_dir/RPMDB" \
        "$top_dir/RPMS" \
        "$top_dir/SOURCES" \
        "$top_dir/SPECS" \
        "$top_dir/SRPMS" \
        "$top_dir/TMP"
    copy_rpm_source "$source_root"
    tar -C "$BUILD_TEMP" -czf "$top_dir/SOURCES/$source_name.tar.gz" \
        "$source_name"
    cp "$PROJECT_DIR/packaging/rpm/brscan-skey-enhanced.spec" \
        "$top_dir/SPECS/"

    rpmbuild \
        --define "_topdir $top_dir" \
        --define "_dbpath $top_dir/RPMDB" \
        --define "_tmppath $top_dir/TMP" \
        --define "pkg_version $VERSION" \
        -bb "$top_dir/SPECS/brscan-skey-enhanced.spec"
    find "$top_dir/RPMS" -type f -name '*.rpm' \
        -exec cp -t "$OUTPUT_DIR" {} +
}

if [ "$BUILD_DEB" -eq 1 ]; then
    build_deb
fi
if [ "$BUILD_RPM" -eq 1 ]; then
    build_rpm
fi

echo "Packages created in $OUTPUT_DIR"
