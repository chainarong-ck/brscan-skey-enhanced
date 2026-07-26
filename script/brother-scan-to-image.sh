#!/bin/bash
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scan-common.sh
source "$SCRIPT_DIR/scan-common.sh"

start_scan image "brscan_image_" "${1:-}" || exit 1
OUTPUT="${BRSCAN_OUTPUT_BASE}.jpg"
convert_scan_to_jpeg "$OUTPUT" || exit 1

if [ -n "$BRSCAN_PRIMARY_OUTPUT" ] &&
    [ -n "${DISPLAY:-}${WAYLAND_DISPLAY:-}" ] &&
    command -v xdg-open >/dev/null 2>&1
then
    xdg-open "$BRSCAN_PRIMARY_OUTPUT" >/dev/null 2>&1 &
fi

exit 0
