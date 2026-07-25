#!/usr/bin/env python3
"""Read, validate, and atomically save Brother scan settings."""

from __future__ import annotations

import configparser
import os
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path


APP_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = APP_DIR / "settings.ini"
PROFILES = ("email", "file", "image")
PROFILE_LABELS = {
    "email": "Scan to Email",
    "file": "Scan to File",
    "image": "Scan to Image",
}
RESOLUTIONS = (100, 150, 200, 300, 600)
PAPER_SIZES = ("A4", "A5", "Letter", "Legal")
DEFAULTS = {
    "email": {"resolution": 150, "paper_size": "A4", "duplex": False},
    "file": {"resolution": 100, "paper_size": "A4", "duplex": False},
    "image": {"resolution": 300, "paper_size": "A4", "duplex": False},
}


class ConfigurationError(ValueError):
    """Raised when a setting is invalid or cannot be read."""


@dataclass(frozen=True)
class ScanSettings:
    resolution: int
    paper_size: str
    duplex: bool


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


def load_all(path: Path = CONFIG_PATH) -> dict[str, ScanSettings]:
    parser = _new_parser()
    if path.exists():
        try:
            with path.open("r", encoding="utf-8") as config_file:
                parser.read_file(config_file)
        except (OSError, configparser.Error) as exc:
            raise ConfigurationError(f"Cannot read {path}: {exc}") from exc

    settings: dict[str, ScanSettings] = {}
    for profile in PROFILES:
        defaults = DEFAULTS[profile]
        resolution = parser.get(
            profile, "resolution", fallback=str(defaults["resolution"])
        )
        paper_size = parser.get(
            profile, "paper_size", fallback=str(defaults["paper_size"])
        )
        try:
            duplex = parser.getboolean(
                profile, "duplex", fallback=bool(defaults["duplex"])
            )
        except ValueError as exc:
            raise ConfigurationError(
                f"Invalid duplex value in [{profile}]."
            ) from exc
        settings[profile] = validate(resolution, paper_size, duplex)
    return settings


def load_profile(profile: str, path: Path = CONFIG_PATH) -> ScanSettings:
    _validate_profile(profile)
    return load_all(path)[profile]


def save_all(
    settings: dict[str, ScanSettings], path: Path = CONFIG_PATH
) -> None:
    parser = _new_parser()
    for profile in PROFILES:
        _validate_profile(profile)
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

    path.parent.mkdir(parents=True, exist_ok=True)
    temp_name: str | None = None
    try:
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


def restore_defaults() -> dict[str, ScanSettings]:
    return {
        profile: validate(
            values["resolution"], values["paper_size"], values["duplex"]
        )
        for profile, values in DEFAULTS.items()
    }


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
