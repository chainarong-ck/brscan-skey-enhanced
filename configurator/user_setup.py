#!/usr/bin/env python3
"""Install the per-user brscan-skey overrides without touching driver files."""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

try:
    from .config_store import CONFIG_PATH, USER_CONFIG_DIR
except ImportError:
    from config_store import CONFIG_PATH, USER_CONFIG_DIR  # type: ignore


APP_DIR = Path(
    os.environ.get(
        "BRSCAN_SKEY_APP_DIR", Path(__file__).resolve().parent.parent
    )
).expanduser()
STATIC_FILES = {
    Path("scantofile.config"): 0o644,
    Path("scantoemail.config"): 0o644,
    Path("scantoimage.config"): 0o644,
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

    for relative_path, mode in STATIC_FILES.items():
        _atomic_copy(
            APP_DIR / relative_path,
            USER_CONFIG_DIR / relative_path,
            mode,
        )

    if not CONFIG_PATH.exists():
        _atomic_copy(DEFAULT_SETTINGS, CONFIG_PATH, 0o600)

    return USER_CONFIG_DIR


def main() -> int:
    try:
        destination = ensure_user_installation()
    except UserSetupError as exc:
        print(f"brscan-skey user setup failed: {exc}", file=sys.stderr)
        return 1

    print(f"User files are ready in {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
