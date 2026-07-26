#!/bin/bash

umask 077

BRSCAN_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BRSCAN_APP_DIR="$(dirname "$BRSCAN_SCRIPT_DIR")"
BRSCAN_INSTALL_PREFIX="$(dirname "$(dirname "$BRSCAN_APP_DIR")")"
BRSCAN_SCANNER="${BRSCAN_SCANNER:-/opt/brother/scanner/brscan-skey/skey-scanimage}"
BRSCAN_SETTINGS_READER="${BRSCAN_SETTINGS_READER:-$BRSCAN_INSTALL_PREFIX/bin/brscan-skey-read-settings}"
BRSCAN_OUTPUT_DIR="${BRSCAN_OUTPUT_DIR:-${HOME:?HOME is not set}/brscan}"
BRSCAN_TEMP=""

if [ -z "${BRSCAN_IMAGE_CONVERTER:-}" ]; then
    if command -v magick >/dev/null 2>&1; then
        BRSCAN_IMAGE_CONVERTER=magick
    elif command -v convert >/dev/null 2>&1; then
        BRSCAN_IMAGE_CONVERTER=convert
    fi
fi

cleanup_scan_temp() {
    if [ -n "$BRSCAN_TEMP" ]; then
        rm -f -- "$BRSCAN_TEMP"
    fi
}

trap cleanup_scan_temp EXIT
trap 'exit 130' HUP INT TERM

brscan_log() {
    local message="$1"
    if command -v logger >/dev/null 2>&1 &&
        logger -t brscan-skey "$message" 2>/dev/null
    then
        return
    fi
    printf 'brscan-skey: %s\n' "$message" >&2
}

load_scan_settings() {
    local profile="$1"
    local output
    local -a values

    if [ ! -x "$BRSCAN_SETTINGS_READER" ]; then
        brscan_log "Settings reader is not installed: $BRSCAN_SETTINGS_READER"
        return 1
    fi

    if ! output="$("$BRSCAN_SETTINGS_READER" "$profile")"; then
        brscan_log "Could not load settings for scan profile: $profile"
        return 1
    fi
    mapfile -t values <<< "$output"

    if [ "${#values[@]}" -ne 3 ]; then
        brscan_log "Invalid settings for scan profile: $profile"
        return 1
    fi

    BRSCAN_RESOLUTION="${values[0]}"
    BRSCAN_PAPER_SIZE="${values[1]}"
    BRSCAN_DUPLEX="${values[2]}"
}

start_scan() {
    local profile="$1"
    local prefix="$2"
    local device="$3"
    local source
    local attempt
    local -a scan_args

    if [ -z "$device" ]; then
        brscan_log "Cannot start scan: scanner device name is missing"
        return 1
    fi
    if [ ! -x "$BRSCAN_SCANNER" ]; then
        brscan_log "Brother scanner command is unavailable: $BRSCAN_SCANNER"
        return 1
    fi
    if ! mkdir -p -- "$BRSCAN_OUTPUT_DIR"; then
        brscan_log "Cannot create scan output directory: $BRSCAN_OUTPUT_DIR"
        return 1
    fi
    if ! chmod 0700 "$BRSCAN_OUTPUT_DIR"; then
        brscan_log "Cannot secure scan output directory: $BRSCAN_OUTPUT_DIR"
        return 1
    fi
    load_scan_settings "$profile" || return 1

    if [ "$BRSCAN_DUPLEX" = "ON" ]; then
        source="ADF_C"
    else
        source="FB"
    fi

    BRSCAN_STAMP="$(date '+%Y-%m-%d_%H-%M-%S_%N')"
    BRSCAN_OUTPUT_BASE="$BRSCAN_OUTPUT_DIR/${prefix}${BRSCAN_STAMP}_$$"
    BRSCAN_TEMP="$BRSCAN_OUTPUT_DIR/.${prefix}${BRSCAN_STAMP}_$$.tif"

    scan_args=(
        --device-name "$device"
        --resolution "$BRSCAN_RESOLUTION"
        --source "$source"
        --size "$BRSCAN_PAPER_SIZE"
        --outputfile "$BRSCAN_TEMP"
    )
    if [ "$BRSCAN_DUPLEX" = "ON" ]; then
        scan_args+=(--duplex)
    fi

    case "$device" in
        *net*) sleep 1 ;;
    esac

    for attempt in 1 2; do
        rm -f -- "$BRSCAN_TEMP"
        "$BRSCAN_SCANNER" "${scan_args[@]}"
        if [ -s "$BRSCAN_TEMP" ]; then
            return 0
        fi
        if [ "$attempt" -eq 1 ]; then
            sleep 1
        fi
    done

    rm -f -- "$BRSCAN_TEMP"
    brscan_log "$profile scan failed: no image was created"
    return 1
}

preserve_scan_as_tiff() {
    local reason="$1"
    local fallback="${BRSCAN_OUTPUT_BASE}.tif"

    if mv -- "$BRSCAN_TEMP" "$fallback"; then
        brscan_log "$reason; TIFF preserved: $fallback"
    else
        brscan_log "$reason; could not preserve temporary TIFF: $BRSCAN_TEMP"
    fi
    return 1
}

convert_scan_to_pdf() {
    local output="$1"
    local action="$2"

    if [ -z "${BRSCAN_IMAGE_CONVERTER:-}" ] ||
        ! command -v "$BRSCAN_IMAGE_CONVERTER" >/dev/null 2>&1
    then
        preserve_scan_as_tiff "$action failed: ImageMagick is unavailable"
        return 1
    fi
    if "$BRSCAN_IMAGE_CONVERTER" "$BRSCAN_TEMP" \
        -units PixelsPerInch \
        -density "$BRSCAN_RESOLUTION" \
        "$output" &&
        [ -s "$output" ]
    then
        rm -f -- "$BRSCAN_TEMP"
        brscan_log "$action saved: $output"
        return 0
    fi

    rm -f -- "$output"
    preserve_scan_as_tiff "$action PDF conversion failed"
}

convert_scan_to_jpeg() {
    local output="$1"

    if [ -z "${BRSCAN_IMAGE_CONVERTER:-}" ] ||
        ! command -v "$BRSCAN_IMAGE_CONVERTER" >/dev/null 2>&1
    then
        preserve_scan_as_tiff "Scan to Image failed: ImageMagick is unavailable"
        return 1
    fi
    if "$BRSCAN_IMAGE_CONVERTER" "$BRSCAN_TEMP" \
        -background white \
        -alpha remove \
        -alpha off \
        -units PixelsPerInch \
        -density "$BRSCAN_RESOLUTION" \
        -quality 92 \
        "$output" &&
        [ -s "$output" ]
    then
        rm -f -- "$BRSCAN_TEMP"
        brscan_log "Scan to Image saved: $output"
        return 0
    fi

    rm -f -- "$output"
    preserve_scan_as_tiff "Scan to Image JPEG conversion failed"
}
