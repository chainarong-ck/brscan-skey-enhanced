from __future__ import annotations

import configparser
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from configurator.config_store import (
    PAPER_SIZES,
    RESOLUTIONS,
    ConfigurationError,
    create_default_settings,
    load_all,
    load_enhanced_enabled,
    load_profile,
    save_enhanced_enabled,
    validate,
)


PROJECT_DIR = Path(__file__).resolve().parent.parent


class PerUserConfigurationTests(unittest.TestCase):
    def test_all_supported_scan_options_are_accepted(self) -> None:
        self.assertEqual(
            RESOLUTIONS,
            (100, 150, 200, 300, 400, 600, 1200),
        )
        self.assertEqual(
            PAPER_SIZES,
            ("A3", "A4", "A5", "A6", "Letter", "Legal"),
        )

        for resolution in RESOLUTIONS:
            with self.subTest(resolution=resolution):
                self.assertEqual(
                    validate(resolution, "A4", False).resolution,
                    resolution,
                )
        for paper_size in PAPER_SIZES:
            with self.subTest(paper_size=paper_size):
                self.assertEqual(
                    validate(300, paper_size, False).paper_size,
                    paper_size,
                )

    def test_default_settings_are_complete_and_enabled(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "settings.ini"

            create_default_settings(path)

            self.assertTrue(load_enhanced_enabled(path))
            settings = load_all(path)
            self.assertEqual(settings["email"].resolution, 200)
            self.assertEqual(settings["file"].resolution, 150)
            self.assertEqual(settings["image"].resolution, 300)
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)

    def test_reader_uses_the_calling_users_home(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            home = Path(temp_dir)
            config_path = home / ".brscan-skey/settings.ini"
            create_default_settings(config_path)
            parser = configparser.ConfigParser()
            parser.read(config_path, encoding="utf-8")
            parser["email"] = {
                "resolution": "600",
                "paper_size": "Legal",
                "duplex": "true",
            }
            with config_path.open("w", encoding="utf-8") as config_file:
                parser.write(config_file)

            environment = os.environ.copy()
            environment["HOME"] = str(home)
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "configurator.config_store",
                    "email",
                ],
                cwd=PROJECT_DIR,
                env=environment,
                check=False,
                capture_output=True,
                text=True,
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "600\nLegal\nON\n")

    def test_reader_rejects_missing_settings_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            environment = os.environ.copy()
            environment["HOME"] = temp_dir
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "configurator.config_store",
                    "file",
                ],
                cwd=PROJECT_DIR,
                env=environment,
                check=False,
                capture_output=True,
                text=True,
            )

        self.assertEqual(result.returncode, 1)
        self.assertIn("Configuration file not found", result.stderr)

    def test_incomplete_configuration_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "settings.ini"
            path.write_text(
                "[general]\nenhanced_enabled = true\n",
                encoding="utf-8",
            )

            with self.assertRaises(ConfigurationError):
                load_all(path)

    def test_reader_validates_only_the_requested_profile(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "settings.ini"
            create_default_settings(path)
            parser = configparser.ConfigParser()
            parser.read(path, encoding="utf-8")
            parser["image"]["resolution"] = "invalid"
            with path.open("w", encoding="utf-8") as config_file:
                parser.write(config_file)

            file_settings = load_profile("file", path)

            self.assertEqual(file_settings.resolution, 150)
            with self.assertRaises(ConfigurationError):
                load_profile("image", path)

    def test_saving_disabled_state_preserves_scan_profiles(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "settings.ini"
            create_default_settings(path)
            before = load_all(path)

            save_enhanced_enabled(False, path)

            self.assertFalse(load_enhanced_enabled(path))
            self.assertEqual(load_all(path), before)

    def test_saving_disabled_state_repairs_invalid_profiles(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "settings.ini"
            create_default_settings(path)
            parser = configparser.ConfigParser()
            parser.read(path, encoding="utf-8")
            parser["email"]["resolution"] = "invalid"
            parser["file"] = {
                "resolution": "600",
                "paper_size": "Legal",
                "duplex": "true",
            }
            with path.open("w", encoding="utf-8") as config_file:
                parser.write(config_file)

            save_enhanced_enabled(False, path)

            self.assertFalse(load_enhanced_enabled(path))
            settings = load_all(path)
            self.assertEqual(settings["email"].resolution, 200)
            self.assertEqual(settings["file"].resolution, 600)
            self.assertEqual(settings["file"].paper_size, "Legal")
            self.assertTrue(settings["file"].duplex)

    def test_saving_disabled_state_recovers_unparseable_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "settings.ini"
            path.write_text("[broken\n", encoding="utf-8")

            save_enhanced_enabled(False, path)

            self.assertFalse(load_enhanced_enabled(path))
            settings = load_all(path)
            self.assertEqual(settings["email"].resolution, 200)
            self.assertEqual(settings["file"].resolution, 150)
            self.assertEqual(settings["image"].resolution, 300)


if __name__ == "__main__":
    unittest.main()
