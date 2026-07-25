#!/bin/bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEST_TEMP="$(mktemp -d)"
trap 'rm -rf "$TEST_TEMP"' EXIT

PREFIX="$TEST_TEMP/prefix"
BROTHER_DIR="$TEST_TEMP/brother-script"
mkdir -p "$BROTHER_DIR"

for config_name in scantofile.config scantoimage.config scantoemail.config; do
    printf 'original %s\n' "$config_name" >"$BROTHER_DIR/$config_name"
done

export BRSCAN_INSTALL_PREFIX="$PREFIX"
export BRSCAN_BROTHER_SCRIPT_DIR="$BROTHER_DIR"
export BRSCAN_ALLOW_UNPRIVILEGED_TESTS=1

"$PROJECT_DIR/install.sh" --no-deps

test -x "$PREFIX/bin/brscan-skey-settings"
test -x "$PREFIX/bin/brscan-skey-enhanced-check"
test -x "$PREFIX/bin/brscan-skey-enhanced-integrate"
test -f "$PREFIX/share/applications/brscan-skey-enhanced.desktop"
test -f "$PREFIX/share/icons/hicolor/scalable/apps/brscan-skey-enhanced.svg"
test -f "$PREFIX/lib/brscan-skey-enhanced/configurator/config_store.py"

for config_name in scantofile.config scantoimage.config scantoemail.config; do
    cmp "$PROJECT_DIR/$config_name" "$BROTHER_DIR/$config_name"
    grep -Fq "original $config_name" \
        "$BROTHER_DIR/$config_name.brscan-skey-enhanced.backup"
done

# Reinstalling must not overwrite the original backup.
"$PROJECT_DIR/install.sh" --no-deps --integrate-only
for config_name in scantofile.config scantoimage.config scantoemail.config; do
    grep -Fq "original $config_name" \
        "$BROTHER_DIR/$config_name.brscan-skey-enhanced.backup"
done

"$PROJECT_DIR/uninstall.sh"

test ! -e "$PREFIX/lib/brscan-skey-enhanced"
test ! -e "$PREFIX/share/brscan-skey-enhanced"
test ! -e "$PREFIX/bin/brscan-skey-settings"

for config_name in scantofile.config scantoimage.config scantoemail.config; do
    grep -Fq "original $config_name" "$BROTHER_DIR/$config_name"
    test ! -e "$BROTHER_DIR/$config_name.brscan-skey-enhanced.backup"
done
