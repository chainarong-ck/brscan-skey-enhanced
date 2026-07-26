"""Install the per-user brscan-skey overrides without touching driver files."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

from .config_store import (
    CONFIG_PATH,
    DEFAULT_ENHANCED_ENABLED,
    USER_CONFIG_DIR,
    ConfigurationError,
    create_default_settings,
    load_enhanced_enabled,
    save_enhanced_enabled,
)


APP_DIR = Path(__file__).resolve().parent.parent
OVERRIDE_FILES = (
    Path("scantofile.config"),
    Path("scantoemail.config"),
    Path("scantoimage.config"),
)


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

    if not enabled:
        removed: list[Path] = []
        try:
            for relative_path in OVERRIDE_FILES:
                active_path = USER_CONFIG_DIR / relative_path
                existed = active_path.exists()
                _remove_file(active_path)
                if existed:
                    removed.append(relative_path)
        except UserSetupError:
            for relative_path in removed:
                try:
                    _atomic_copy(
                        APP_DIR / relative_path,
                        USER_CONFIG_DIR / relative_path,
                        0o644,
                    )
                except UserSetupError:
                    pass
            raise
        return

    prepared: list[tuple[Path, bool]] = []
    for relative_path in OVERRIDE_FILES:
        active_path = USER_CONFIG_DIR / relative_path
        existed = active_path.exists()
        try:
            _atomic_copy(APP_DIR / relative_path, active_path, 0o644)
        except UserSetupError:
            for prepared_path, previously_existed in prepared:
                if not previously_existed:
                    try:
                        prepared_path.unlink(missing_ok=True)
                    except OSError:
                        pass
            raise
        prepared.append((active_path, existed))


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
        os.chmod(USER_CONFIG_DIR, 0o700)
    except OSError as exc:
        raise UserSetupError(
            f"Cannot create user directory {USER_CONFIG_DIR}: {exc}"
        ) from exc

    if not CONFIG_PATH.exists():
        try:
            create_default_settings()
        except ConfigurationError as exc:
            raise UserSetupError(str(exc)) from exc

    try:
        enabled = load_enhanced_enabled()
    except ConfigurationError as exc:
        enabled = False
        try:
            save_enhanced_enabled(enabled)
        except ConfigurationError as save_exc:
            raise UserSetupError(str(save_exc)) from exc
    apply_override_state(enabled)

    return USER_CONFIG_DIR
