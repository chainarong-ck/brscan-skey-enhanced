#!/bin/bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEST_TEMP="$(mktemp -d)"
trap 'rm -rf "$TEST_TEMP"' EXIT

export HOME="$TEST_TEMP/home"
export PATH="$PROJECT_DIR/tests/fixtures/bin:$PATH"
export BRSCAN_SCANNER="$PROJECT_DIR/tests/fixtures/bin/skey-scanimage"
export BRSCAN_SETTINGS_PATH="$TEST_TEMP/settings.ini"
export SCAN_CALL_LOG="$TEST_TEMP/scanner.log"
export EMAIL_CALL_LOG="$TEST_TEMP/email.log"
unset DISPLAY WAYLAND_DISPLAY

mkdir -p "$HOME"
: >"$SCAN_CALL_LOG"
: >"$EMAIL_CALL_LOG"

"$PROJECT_DIR/script/brother-scan-to-file.sh" "mock-device"
"$PROJECT_DIR/script/brother-scan-to-image.sh" "mock-device"
"$PROJECT_DIR/script/brother-scan-to-email.sh" "mock-device"

find "$HOME/brscan" -maxdepth 1 -type f -name 'brscan_file_*.pdf' |
    grep -q .
find "$HOME/brscan" -maxdepth 1 -type f -name 'brscan_image_*.jpg' |
    grep -q .
find "$HOME/brscan" -maxdepth 1 -type f -name 'brscan_email_*.pdf' |
    grep -q .

test "$(find "$HOME/brscan" -maxdepth 1 -type f | wc -l)" -eq 3
test "$(wc -l <"$SCAN_CALL_LOG")" -eq 3
test "$(wc -l <"$EMAIL_CALL_LOG")" -eq 1

grep -Fq -- '--device-name mock-device' "$SCAN_CALL_LOG"
grep -Fq -- '--resolution 100' "$SCAN_CALL_LOG"
grep -Fq -- '--resolution 150' "$SCAN_CALL_LOG"
grep -Fq -- '--resolution 300' "$SCAN_CALL_LOG"
grep -Fq -- '--source FB' "$SCAN_CALL_LOG"
grep -Fq -- '--size A4' "$SCAN_CALL_LOG"

if grep -Fq -- '--duplex' "$SCAN_CALL_LOG"; then
    echo "Default profiles must not enable duplex scanning" >&2
    exit 1
fi
