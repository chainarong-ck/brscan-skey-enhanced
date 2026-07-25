from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from configurator.config_store import (
    load_all,
    load_enhanced_enabled,
    save_enhanced_enabled,
)


PROJECT_DIR = Path(__file__).resolve().parent.parent


class PerUserConfigurationTests(unittest.TestCase):
    def test_reader_uses_the_calling_users_home(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            home = Path(temp_dir)
            config_dir = home / ".brscan-skey"
            config_dir.mkdir()
            (config_dir / "settings.ini").write_text(
                "[email]\n"
                "resolution = 600\n"
                "paper_size = Legal\n"
                "duplex = true\n",
                encoding="utf-8",
            )
            result = subprocess.run(
                [
                    sys.executable,
                    str(PROJECT_DIR / "configurator/config_store.py"),
                    "email",
                ],
                env={"HOME": str(home), "PATH": "/usr/bin:/bin"},
                check=False,
                capture_output=True,
                text=True,
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "600\nLegal\nON\n")

    def test_missing_file_uses_shipped_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            result = subprocess.run(
                [
                    sys.executable,
                    str(PROJECT_DIR / "configurator/config_store.py"),
                    "file",
                ],
                env={"HOME": temp_dir, "PATH": "/usr/bin:/bin"},
                check=False,
                capture_output=True,
                text=True,
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "150\nA4\nOFF\n")

    def test_enhanced_actions_default_to_enabled(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "settings.ini"
            self.assertTrue(load_enhanced_enabled(path))

    def test_saving_disabled_state_preserves_scan_profiles(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "settings.ini"
            path.write_text(
                "[file]\n"
                "resolution = 600\n"
                "paper_size = Legal\n"
                "duplex = true\n",
                encoding="utf-8",
            )

            save_enhanced_enabled(False, path)

            self.assertFalse(load_enhanced_enabled(path))
            file_settings = load_all(path)["file"]
            self.assertEqual(file_settings.resolution, 600)
            self.assertEqual(file_settings.paper_size, "Legal")
            self.assertTrue(file_settings.duplex)


if __name__ == "__main__":
    unittest.main()
