#!/bin/bash
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scan-common.sh
source "$SCRIPT_DIR/scan-common.sh"

start_scan file "brscan_file_" "${1:-}" || exit 1
OUTPUT="${BRSCAN_OUTPUT_BASE}.pdf"
convert_scan_to_pdf "$OUTPUT" "Scan to File"
