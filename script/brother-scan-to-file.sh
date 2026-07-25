#!/bin/bash
set -u

OUTDIR="$HOME/brscan"
STAMP="$(date +%Y-%m-%d_%H-%M-%S)"
SCANNER="${BRSCAN_SCANNER:-/opt/brother/scanner/brscan-skey/skey-scanimage}"
DEVICE="${1:-}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=script/load-scan-settings.sh
source "$SCRIPT_DIR/load-scan-settings.sh"
load_scan_settings file || exit 1

PREFIX="brscan_file_"
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
    logger -t brscan-skey "Scan to File failed: no image created"
    exit 1
fi

if convert_scan_output "$OUTPUT_TEMP" \
    -units PixelsPerInch \
    -density "$RESOLUTION" \
    "$OUTPUT"
then
    rm -f "$OUTPUT_TEMP"
    logger -t brscan-skey "Scan to File saved: $OUTPUT"
    exit 0
fi

FALLBACK="$OUTDIR/${PREFIX}${STAMP}.tif"
mv "$OUTPUT_TEMP" "$FALLBACK"
logger -t brscan-skey \
    "PDF conversion failed; TIFF preserved: $FALLBACK"
exit 1
