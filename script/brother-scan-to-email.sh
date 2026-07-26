#!/bin/bash
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scan-common.sh
source "$SCRIPT_DIR/scan-common.sh"

start_scan email "brscan_email_" "${1:-}" || exit 1
OUTPUT="${BRSCAN_OUTPUT_BASE}.pdf"
convert_scan_to_pdf "$OUTPUT" "Scan to Email" || exit 1

if command -v xdg-email >/dev/null 2>&1; then
    if xdg-email \
        --utf8 \
        --attach "$OUTPUT" \
        --subject "Scanned document ${BRSCAN_STAMP}" \
        --body "Scanned document saved at: $OUTPUT" \
        >/dev/null 2>&1
    then
        brscan_log "Opened the default email composer with attachment: $OUTPUT"
    else
        brscan_log "Could not open the email composer; PDF preserved: $OUTPUT"
    fi
else
    brscan_log "xdg-email is unavailable; PDF preserved: $OUTPUT"
fi

exit 0
