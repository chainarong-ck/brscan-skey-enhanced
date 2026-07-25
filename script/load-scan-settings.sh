#!/bin/bash

# Load validated settings into RESOLUTION, SIZE, and DUPLEX.
load_scan_settings() {
    local profile="$1"
    local reader
    local -a values

    if [ -n "${BRSCAN_SKEY_SETTINGS_READER:-}" ]; then
        reader="$BRSCAN_SKEY_SETTINGS_READER"
    elif [ -x /usr/local/bin/brscan-skey-read-settings ]; then
        reader=/usr/local/bin/brscan-skey-read-settings
    elif [ -x /usr/bin/brscan-skey-read-settings ]; then
        reader=/usr/bin/brscan-skey-read-settings
    elif command -v brscan-skey-read-settings >/dev/null 2>&1; then
        reader="$(command -v brscan-skey-read-settings)"
    else
        logger -t brscan-skey \
            "brscan-skey-read-settings is not installed"
        return 1
    fi

    if ! mapfile -t values < <(
        "$reader" "$profile"
    ); then
        logger -t brscan-skey \
            "Could not load settings for scan profile: $profile"
        return 1
    fi

    if [ "${#values[@]}" -ne 3 ]; then
        logger -t brscan-skey \
            "Invalid setting count for scan profile: $profile"
        return 1
    fi

    RESOLUTION="${values[0]}"
    SIZE="${values[1]}"
    DUPLEX="${values[2]}"
}
