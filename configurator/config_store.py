"""Read, validate, and atomically save Brother scan settings."""

from __future__ import annotations

import configparser
import os
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path


USER_CONFIG_DIR = Path.home() / ".brscan-skey"
CONFIG_PATH = USER_CONFIG_DIR / "settings.ini"
DEFAULT_ENHANCED_ENABLED = True
PROFILES = ("email", "file", "image")
PROFILE_LABELS = {
    "email": "Scan to Email",
    "file": "Scan to File",
    "image": "Scan to Image",
}
RESOLUTIONS = (100, 150, 200, 300, 400, 600, 1200, 2400, 4800, 9600)
PAPER_SIZES = ("A3", "A4", "A5", "A6", "Letter", "Legal")


class ConfigurationError(Exception):
    """Raised when a setting is invalid or cannot be read."""


@dataclass(frozen=True)
class ScanSettings:
    resolution: int
    paper_size: str
    duplex: bool


DEFAULTS: dict[str, ScanSettings] = {
    "email": ScanSettings(200, "A4", False),
    "file": ScanSettings(150, "A4", False),
    "image": ScanSettings(300, "A4", False),
}


def _validate_profile(profile: str) -> None:
    if profile not in PROFILES:
        raise ConfigurationError(f"Unknown scan profile: {profile}")


def validate(resolution: object, paper_size: object, duplex: object) -> ScanSettings:
    try:
        resolution_value = int(resolution)
    except (TypeError, ValueError) as exc:
        raise ConfigurationError("Resolution must be a number.") from exc

    if resolution_value not in RESOLUTIONS:
        allowed = ", ".join(str(value) for value in RESOLUTIONS)
        raise ConfigurationError(f"Resolution must be one of: {allowed} DPI.")

    paper_value = str(paper_size)
    if paper_value not in PAPER_SIZES:
        raise ConfigurationError(
            f"Paper size must be one of: {', '.join(PAPER_SIZES)}."
        )

    if not isinstance(duplex, bool):
        raise ConfigurationError("Duplex must be true or false.")

    return ScanSettings(resolution_value, paper_value, duplex)


def _new_parser() -> configparser.ConfigParser:
    parser = configparser.ConfigParser(interpolation=None)
    parser.optionxform = str.lower
    return parser


def _read_parser(path: Path) -> configparser.ConfigParser:
    if not path.is_file():
        raise ConfigurationError(f"Configuration file not found: {path}")

    parser = _new_parser()
    try:
        with path.open("r", encoding="utf-8") as config_file:
            parser.read_file(config_file)
    except (OSError, configparser.Error) as exc:
        raise ConfigurationError(f"Cannot read {path}: {exc}") from exc
    return parser


def load_enhanced_enabled(path: Path = CONFIG_PATH) -> bool:
    parser = _read_parser(path)
    try:
        return parser.getboolean("general", "enhanced_enabled")
    except (configparser.Error, ValueError) as exc:
        raise ConfigurationError(
            "Missing or invalid enhanced_enabled value in [general]."
        ) from exc


def _load_profile_from_parser(
    parser: configparser.ConfigParser, profile: str
) -> ScanSettings:
    try:
        resolution = parser.get(profile, "resolution")
        paper_size = parser.get(profile, "paper_size")
        duplex = parser.getboolean(profile, "duplex")
    except (configparser.Error, ValueError) as exc:
        raise ConfigurationError(
            f"Missing or invalid setting in [{profile}]."
        ) from exc
    return validate(resolution, paper_size, duplex)


def load_all(path: Path = CONFIG_PATH) -> dict[str, ScanSettings]:
    parser = _read_parser(path)
    return {
        profile: _load_profile_from_parser(parser, profile)
        for profile in PROFILES
    }


def load_profile(profile: str, path: Path = CONFIG_PATH) -> ScanSettings:
    _validate_profile(profile)
    return _load_profile_from_parser(_read_parser(path), profile)


def _write_parser(
    parser: configparser.ConfigParser, path: Path
) -> None:
    temp_name: str | None = None
    try:
        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            delete=False,
        ) as temp_file:
            temp_name = temp_file.name
            parser.write(temp_file)
            temp_file.flush()
            os.fsync(temp_file.fileno())
        os.replace(temp_name, path)
        os.chmod(path, 0o600)
    except OSError as exc:
        if temp_name:
            try:
                os.unlink(temp_name)
            except OSError:
                pass
        raise ConfigurationError(f"Cannot save {path}: {exc}") from exc


def save_all(
    settings: dict[str, ScanSettings],
    path: Path = CONFIG_PATH,
    *,
    enhanced_enabled: bool | None = None,
) -> None:
    if enhanced_enabled is None:
        enhanced_enabled = load_enhanced_enabled(path)
    if not isinstance(enhanced_enabled, bool):
        raise ConfigurationError(
            "Enhanced enabled state must be true or false."
        )

    parser = _new_parser()
    parser["general"] = {
        "enhanced_enabled": "true" if enhanced_enabled else "false"
    }
    for profile in PROFILES:
        if profile not in settings:
            raise ConfigurationError(f"Missing scan profile: {profile}")
        value = validate(
            settings[profile].resolution,
            settings[profile].paper_size,
            settings[profile].duplex,
        )
        parser[profile] = {
            "resolution": str(value.resolution),
            "paper_size": value.paper_size,
            "duplex": "true" if value.duplex else "false",
        }

    _write_parser(parser, path)


def save_enhanced_enabled(
    enabled: bool, path: Path = CONFIG_PATH
) -> None:
    if not isinstance(enabled, bool):
        raise ConfigurationError(
            "Enhanced enabled state must be true or false."
        )
    save_all(load_all(path), path, enhanced_enabled=enabled)


def restore_defaults() -> dict[str, ScanSettings]:
    return dict(DEFAULTS)


def create_default_settings(path: Path = CONFIG_PATH) -> None:
    save_all(
        restore_defaults(),
        path,
        enhanced_enabled=DEFAULT_ENHANCED_ENABLED,
    )


def export_for_scanner(profile: str) -> int:
    """Internal shell bridge: print validated values, one per line."""
    try:
        settings = load_profile(profile)
    except ConfigurationError as exc:
        print(f"brscan settings error: {exc}", file=sys.stderr)
        return 1

    print(settings.resolution)
    print(settings.paper_size)
    print("ON" if settings.duplex else "OFF")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("This is an internal helper.", file=sys.stderr)
        raise SystemExit(2)
    raise SystemExit(export_for_scanner(sys.argv[1]))
