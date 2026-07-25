import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from configurator import config_store
from configurator.config_store import (
    DEFAULTS,
    PROFILES,
    ConfigurationError,
    ScanSettings,
    load_all,
    load_profile,
    restore_defaults,
    save_all,
    validate,
)


class ConfigStoreTests(unittest.TestCase):
    def test_missing_file_uses_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            settings = load_all(Path(temp_dir) / "missing.ini")

        self.assertEqual(settings, restore_defaults())

    def test_settings_round_trip(self) -> None:
        settings = {
            "email": ScanSettings(200, "Letter", True),
            "file": ScanSettings(300, "Legal", False),
            "image": ScanSettings(600, "A5", True),
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "settings.ini"
            save_all(settings, path)
            loaded = load_all(path)
            mode = path.stat().st_mode & 0o777

        self.assertEqual(loaded, settings)
        self.assertEqual(mode, 0o600)

    def test_partial_file_uses_profile_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "settings.ini"
            path.write_text("[email]\nresolution = 600\n", encoding="utf-8")
            settings = load_all(path)

        self.assertEqual(settings["email"].resolution, 600)
        self.assertEqual(settings["email"].paper_size, DEFAULTS["email"]["paper_size"])
        self.assertEqual(settings["file"], restore_defaults()["file"])

    def test_legacy_repository_settings_are_still_loaded(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "new" / "settings.ini"
            legacy_path = Path(temp_dir) / "legacy.ini"
            legacy_path.write_text(
                "[image]\nresolution = 600\npaper_size = Letter\n",
                encoding="utf-8",
            )
            with (
                patch.object(config_store, "CONFIG_PATH", config_path),
                patch.object(config_store, "LEGACY_CONFIG_PATH", legacy_path),
            ):
                settings = load_all(config_path)

        self.assertEqual(settings["image"].resolution, 600)
        self.assertEqual(settings["image"].paper_size, "Letter")

    def test_invalid_values_are_rejected(self) -> None:
        invalid_values = (
            (72, "A4", False),
            (300, "B4", False),
            (300, "A4", "false"),
        )

        for values in invalid_values:
            with self.subTest(values=values):
                with self.assertRaises(ConfigurationError):
                    validate(*values)

    def test_invalid_profile_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaises(ConfigurationError):
                load_profile("unknown", Path(temp_dir) / "settings.ini")

    def test_save_requires_every_profile(self) -> None:
        incomplete = {
            profile: restore_defaults()[profile]
            for profile in PROFILES
            if profile != "image"
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaises(ConfigurationError):
                save_all(incomplete, Path(temp_dir) / "settings.ini")


if __name__ == "__main__":
    unittest.main()
