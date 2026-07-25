from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent.parent


class UserSetupTests(unittest.TestCase):
    def _run_setup(self, home: Path) -> subprocess.CompletedProcess[str]:
        environment = os.environ.copy()
        environment["HOME"] = str(home)
        environment["BRSCAN_SKEY_APP_DIR"] = str(PROJECT_DIR)
        return subprocess.run(
            [
                sys.executable,
                str(PROJECT_DIR / "configurator/user_setup.py"),
            ],
            env=environment,
            check=False,
            capture_output=True,
            text=True,
        )

    def test_setup_installs_managed_files_and_default_settings(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            home = Path(temp_dir)
            result = self._run_setup(home)
            user_dir = home / ".brscan-skey"

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((user_dir / "scantofile.config").is_file())
            self.assertTrue(
                (user_dir / "script/brother-scan-to-file.sh").is_file()
            )
            self.assertTrue((user_dir / "settings.ini").is_file())
            self.assertEqual(
                (user_dir / "settings.ini").read_text(encoding="utf-8"),
                (PROJECT_DIR / "settings.ini.example").read_text(
                    encoding="utf-8"
                ),
            )
            self.assertTrue(
                (user_dir / "script/brother-scan-to-file.sh").stat().st_mode
                & 0o100
            )
            self.assertEqual(
                (user_dir / "settings.ini").stat().st_mode & 0o777,
                0o600,
            )

    def test_setup_preserves_existing_user_settings(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            home = Path(temp_dir)
            user_dir = home / ".brscan-skey"
            user_dir.mkdir()
            settings = user_dir / "settings.ini"
            custom_content = (
                "[file]\nresolution = 600\npaper_size = Legal\nduplex = true\n"
            )
            settings.write_text(custom_content, encoding="utf-8")

            result = self._run_setup(home)

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(settings.read_text(encoding="utf-8"), custom_content)

    def test_setup_refreshes_managed_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            home = Path(temp_dir)
            user_dir = home / ".brscan-skey"
            user_dir.mkdir()
            managed_file = user_dir / "scantofile.config"
            managed_file.write_text("outdated\n", encoding="utf-8")

            result = self._run_setup(home)

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(
                managed_file.read_text(encoding="utf-8"),
                (PROJECT_DIR / "scantofile.config").read_text(
                    encoding="utf-8"
                ),
            )


if __name__ == "__main__":
    unittest.main()
