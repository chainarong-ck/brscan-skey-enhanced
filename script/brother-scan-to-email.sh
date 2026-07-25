#!/bin/bash
set -u

OUTDIR="$HOME/brscan"
STAMP="$(date +%Y-%m-%d_%H-%M-%S)"
SCANNER="${BRSCAN_SCANNER:-/opt/brother/scanner/brscan-skey/skey-scanimage}"
DEVICE="${1:-}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=script/load-scan-settings.sh
source "$SCRIPT_DIR/load-scan-settings.sh"
load_scan_settings email || exit 1

PREFIX="brscan_email_"
OUTPUT="$OUTDIR/${PREFIX}${STAMP}.pdf"
OUTPUT_TEMP="$OUTDIR/.${PREFIX}${STAMP}-$$.tif"

mkdir -p "$OUTDIR"

if [ "$DUPLEX" = 'ON' ]; then
    SOURCE="ADF_C"
else
    SOURCE="FB"
fi

SCAN_ARGS=(
    --device-name "$DEVICE"
    --resolution "$RESOLUTION"
    --source "$SOURCE"
    --size "$SIZE"
    --outputfile "$OUTPUT_TEMP"
)
if [ "$DUPLEX" = 'ON' ]; then
    SCAN_ARGS+=(--duplex)
fi

"$SCANNER" "${SCAN_ARGS[@]}"
if [ ! -s "$OUTPUT_TEMP" ]; then
    rm -f "$OUTPUT_TEMP"
    sleep 1
    "$SCANNER" "${SCAN_ARGS[@]}"
fi

if [ ! -s "$OUTPUT_TEMP" ]; then
    logger -t brscan-skey "Scan to Email failed: no image created"
    exit 1
fi

if convert_scan_output "$OUTPUT_TEMP" \
    -units PixelsPerInch \
    -density "$RESOLUTION" \
    "$OUTPUT"
then
    rm -f "$OUTPUT_TEMP"
    logger -t brscan-skey "Scan to Email saved: $OUTPUT"
else
    FALLBACK="$OUTDIR/${PREFIX}${STAMP}.tif"
    mv "$OUTPUT_TEMP" "$FALLBACK"
    logger -t brscan-skey \
        "Email PDF conversion failed; TIFF preserved: $FALLBACK"
    exit 1
fi

if command -v xdg-email >/dev/null 2>&1; then
    xdg-email \
        --utf8 \
        --subject "Scanned document ${STAMP}" \
        --body "Scanned document saved at: $OUTPUT" \
        >/dev/null 2>&1 &
    logger -t brscan-skey \
        "Opened default email composer with scanned file path: $OUTPUT"
else
    logger -t brscan-skey \
        "xdg-email is unavailable; PDF preserved: $OUTPUT"
fi

exit 0
