#!/bin/bash

# These variables are intentionally assigned for the scripts that source this file.
# shellcheck disable=SC2034

# Load validated settings into RESOLUTION, SIZE, and DUPLEX.
load_scan_settings() {
    local profile="$1"
    local app_dir
    local -a values

    app_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
    if ! mapfile -t values < <(
        python3 "$app_dir/configurator/config_store.py" "$profile"
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
