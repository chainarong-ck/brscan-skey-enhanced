#!/usr/bin/env python3
"""Install the per-user brscan-skey overrides without touching driver files."""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

try:
    from .config_store import (
        CONFIG_PATH,
        DEFAULT_ENHANCED_ENABLED,
        USER_CONFIG_DIR,
        ConfigurationError,
        load_enhanced_enabled,
        save_enhanced_enabled,
    )
except ImportError:
    from config_store import (  # type: ignore
        CONFIG_PATH,
        DEFAULT_ENHANCED_ENABLED,
        USER_CONFIG_DIR,
        ConfigurationError,
        load_enhanced_enabled,
        save_enhanced_enabled,
    )


APP_DIR = Path(
    os.environ.get(
        "BRSCAN_SKEY_APP_DIR", Path(__file__).resolve().parent.parent
    )
).expanduser()
OVERRIDE_FILES = (
    Path("scantofile.config"),
    Path("scantoemail.config"),
    Path("scantoimage.config"),
)
SCRIPT_FILES = {
    Path("script/load-scan-settings.sh"): 0o755,
    Path("script/brother-scan-to-file.sh"): 0o755,
    Path("script/brother-scan-to-email.sh"): 0o755,
    Path("script/brother-scan-to-image.sh"): 0o755,
}
DEFAULT_SETTINGS = APP_DIR / "settings.ini.example"


class UserSetupError(OSError):
    """Raised when the user's brscan-skey files cannot be installed."""


def _atomic_copy(source: Path, destination: Path, mode: int) -> None:
    try:
        data = source.read_bytes()
    except OSError as exc:
        raise UserSetupError(f"Cannot read installed file {source}: {exc}") from exc

    temp_name: str | None = None
    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            "wb",
            dir=destination.parent,
            prefix=f".{destination.name}.",
            delete=False,
        ) as temp_file:
            temp_name = temp_file.name
            temp_file.write(data)
            temp_file.flush()
            os.fsync(temp_file.fileno())
        os.chmod(temp_name, mode)
        os.replace(temp_name, destination)
    except OSError as exc:
        if temp_name:
            try:
                os.unlink(temp_name)
            except OSError:
                pass
        raise UserSetupError(f"Cannot install {destination}: {exc}") from exc


def _remove_file(path: Path) -> None:
    try:
        path.unlink(missing_ok=True)
    except OSError as exc:
        raise UserSetupError(f"Cannot remove managed file {path}: {exc}") from exc


def apply_override_state(enabled: bool) -> None:
    """Activate all overrides or deactivate all of them as one feature."""
    if not isinstance(enabled, bool):
        raise UserSetupError("Enhanced enabled state must be true or false.")

    prepared: list[tuple[Path, bool]] = []
    opposite_paths: list[Path] = []
    for relative_path in OVERRIDE_FILES:
        active_path = USER_CONFIG_DIR / relative_path
        disabled_path = active_path.with_name(f"{active_path.name}.disabled")
        if enabled:
            target_path = active_path
            opposite_path = disabled_path
        else:
            target_path = disabled_path
            opposite_path = active_path

        existed = target_path.exists()
        try:
            _atomic_copy(APP_DIR / relative_path, target_path, 0o644)
        except UserSetupError:
            for prepared_path, previously_existed in prepared:
                if not previously_existed:
                    try:
                        prepared_path.unlink(missing_ok=True)
                    except OSError:
                        pass
            raise
        prepared.append((target_path, existed))
        opposite_paths.append(opposite_path)

    for opposite_path in opposite_paths:
        _remove_file(opposite_path)


def set_enhanced_enabled(enabled: bool) -> None:
    """Persist the requested state and synchronize all override files."""
    try:
        previous = load_enhanced_enabled()
    except ConfigurationError:
        previous = DEFAULT_ENHANCED_ENABLED

    apply_override_state(enabled)
    try:
        save_enhanced_enabled(enabled)
    except ConfigurationError:
        try:
            apply_override_state(previous)
        except UserSetupError:
            pass
        raise


def ensure_user_installation() -> Path:
    """Refresh managed files and create settings.ini only when it is absent."""
    try:
        USER_CONFIG_DIR.mkdir(mode=0o700, parents=True, exist_ok=True)
        (USER_CONFIG_DIR / "script").mkdir(
            mode=0o755, parents=True, exist_ok=True
        )
    except OSError as exc:
        raise UserSetupError(
            f"Cannot create user directory {USER_CONFIG_DIR}: {exc}"
        ) from exc

    if not CONFIG_PATH.exists():
        _atomic_copy(DEFAULT_SETTINGS, CONFIG_PATH, 0o600)

    for relative_path, mode in SCRIPT_FILES.items():
        _atomic_copy(
            APP_DIR / relative_path,
            USER_CONFIG_DIR / relative_path,
            mode,
        )

    try:
        enabled = load_enhanced_enabled()
    except ConfigurationError:
        enabled = DEFAULT_ENHANCED_ENABLED
    apply_override_state(enabled)

    return USER_CONFIG_DIR


def main() -> int:
    try:
        destination = ensure_user_installation()
    except (ConfigurationError, UserSetupError) as exc:
        print(f"brscan-skey user setup failed: {exc}", file=sys.stderr)
        return 1

    try:
        enabled = load_enhanced_enabled()
    except ConfigurationError:
        enabled = DEFAULT_ENHANCED_ENABLED
    state = "enabled" if enabled else "disabled"
    print(f"User files are ready in {destination} (enhanced actions: {state})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
