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

    def _run_toggle(
        self, home: Path, enabled: bool
    ) -> subprocess.CompletedProcess[str]:
        environment = os.environ.copy()
        environment["HOME"] = str(home)
        environment["BRSCAN_SKEY_APP_DIR"] = str(PROJECT_DIR)
        return subprocess.run(
            [
                sys.executable,
                "-c",
                "from configurator.user_setup import "
                "set_enhanced_enabled; "
                f"set_enhanced_enabled({enabled!r})",
            ],
            cwd=PROJECT_DIR,
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
            self.assertFalse((user_dir / "script").exists())
            self.assertTrue((user_dir / "settings.ini").is_file())
            self.assertEqual(
                (user_dir / "settings.ini").read_text(encoding="utf-8"),
                (PROJECT_DIR / "settings.ini.example").read_text(
                    encoding="utf-8"
                ),
            )
            self.assertIn(
                "/usr/local/lib/brscan-skey-enhanced/script/"
                "brother-scan-to-file.sh",
                (user_dir / "scantofile.config").read_text(
                    encoding="utf-8"
                ),
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

    def test_setup_removes_only_legacy_managed_user_scripts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            home = Path(temp_dir)
            script_dir = home / ".brscan-skey/script"
            script_dir.mkdir(parents=True)
            legacy_names = (
                "load-scan-settings.sh",
                "brother-scan-to-file.sh",
                "brother-scan-to-email.sh",
                "brother-scan-to-image.sh",
            )
            for name in legacy_names:
                (script_dir / name).write_text("old\n", encoding="utf-8")
            custom_script = script_dir / "keep-my-script.sh"
            custom_script.write_text("custom\n", encoding="utf-8")

            result = self._run_setup(home)

            self.assertEqual(result.returncode, 0, result.stderr)
            for name in legacy_names:
                self.assertFalse((script_dir / name).exists())
            self.assertEqual(
                custom_script.read_text(encoding="utf-8"),
                "custom\n",
            )

    def test_disabled_state_deactivates_all_override_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            home = Path(temp_dir)
            user_dir = home / ".brscan-skey"
            user_dir.mkdir()
            settings = user_dir / "settings.ini"
            settings.write_text(
                "[general]\nenhanced_enabled = false\n",
                encoding="utf-8",
            )

            result = self._run_setup(home)

            self.assertEqual(result.returncode, 0, result.stderr)
            for name in (
                "scantofile.config",
                "scantoemail.config",
                "scantoimage.config",
            ):
                self.assertFalse((user_dir / name).exists())
                self.assertTrue((user_dir / f"{name}.disabled").is_file())

    def test_reenabling_restores_all_override_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            home = Path(temp_dir)
            user_dir = home / ".brscan-skey"
            setup_result = self._run_setup(home)
            disabled_result = self._run_toggle(home, False)

            self.assertEqual(setup_result.returncode, 0, setup_result.stderr)
            self.assertEqual(disabled_result.returncode, 0, disabled_result.stderr)
            self.assertIn(
                "enhanced_enabled = false",
                (user_dir / "settings.ini").read_text(encoding="utf-8"),
            )
            for name in (
                "scantofile.config",
                "scantoemail.config",
                "scantoimage.config",
            ):
                self.assertFalse((user_dir / name).exists())
                self.assertTrue((user_dir / f"{name}.disabled").is_file())

            enabled_result = self._run_toggle(home, True)

            self.assertEqual(enabled_result.returncode, 0, enabled_result.stderr)
            self.assertIn(
                "enhanced_enabled = true",
                (user_dir / "settings.ini").read_text(encoding="utf-8"),
            )
            for name in (
                "scantofile.config",
                "scantoemail.config",
                "scantoimage.config",
            ):
                self.assertTrue((user_dir / name).is_file())
                self.assertFalse((user_dir / f"{name}.disabled").exists())


if __name__ == "__main__":
    unittest.main()
