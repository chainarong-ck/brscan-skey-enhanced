from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent.parent
OVERRIDE_NAMES = (
    "scantofile.config",
    "scantoemail.config",
    "scantoimage.config",
)


class UserSetupTests(unittest.TestCase):
    def _run_python(
        self, home: Path, statement: str
    ) -> subprocess.CompletedProcess[str]:
        environment = os.environ.copy()
        environment["HOME"] = str(home)
        return subprocess.run(
            [sys.executable, "-c", statement],
            cwd=PROJECT_DIR,
            env=environment,
            check=False,
            capture_output=True,
            text=True,
        )

    def _run_setup(self, home: Path) -> subprocess.CompletedProcess[str]:
        return self._run_python(
            home,
            "from configurator.user_setup import "
            "ensure_user_installation; ensure_user_installation()",
        )

    def _run_toggle(
        self, home: Path, enabled: bool
    ) -> subprocess.CompletedProcess[str]:
        return self._run_python(
            home,
            "from configurator.user_setup import "
            "set_enhanced_enabled; "
            f"set_enhanced_enabled({enabled!r})",
        )

    def test_first_launch_creates_only_user_specific_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            home = Path(temp_dir)

            result = self._run_setup(home)

            user_dir = home / ".brscan-skey"
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(user_dir.stat().st_mode & 0o777, 0o700)
            self.assertTrue((user_dir / "settings.ini").is_file())
            self.assertEqual(
                (user_dir / "settings.ini").stat().st_mode & 0o777,
                0o600,
            )
            self.assertFalse((user_dir / "script").exists())
            for name in OVERRIDE_NAMES:
                self.assertEqual(
                    (user_dir / name).read_text(encoding="utf-8"),
                    (PROJECT_DIR / name).read_text(encoding="utf-8"),
                )

    def test_setup_preserves_valid_user_settings(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            home = Path(temp_dir)
            first_result = self._run_setup(home)
            settings_path = home / ".brscan-skey/settings.ini"
            custom_content = settings_path.read_text(encoding="utf-8").replace(
                "resolution = 150",
                "resolution = 600",
            )
            settings_path.write_text(custom_content, encoding="utf-8")

            second_result = self._run_setup(home)

            self.assertEqual(first_result.returncode, 0, first_result.stderr)
            self.assertEqual(second_result.returncode, 0, second_result.stderr)
            self.assertEqual(
                settings_path.read_text(encoding="utf-8"),
                custom_content,
            )

    def test_setup_refreshes_managed_override_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            home = Path(temp_dir)
            first_result = self._run_setup(home)
            managed_file = home / ".brscan-skey/scantofile.config"
            managed_file.write_text("outdated\n", encoding="utf-8")

            second_result = self._run_setup(home)

            self.assertEqual(first_result.returncode, 0, first_result.stderr)
            self.assertEqual(second_result.returncode, 0, second_result.stderr)
            self.assertEqual(
                managed_file.read_text(encoding="utf-8"),
                (PROJECT_DIR / "scantofile.config").read_text(
                    encoding="utf-8"
                ),
            )

    def test_global_toggle_disables_and_reenables_all_overrides(self) -> None:
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
            for name in OVERRIDE_NAMES:
                self.assertFalse((user_dir / name).exists())

            enabled_result = self._run_toggle(home, True)

            self.assertEqual(enabled_result.returncode, 0, enabled_result.stderr)
            self.assertIn(
                "enhanced_enabled = true",
                (user_dir / "settings.ini").read_text(encoding="utf-8"),
            )
            for name in OVERRIDE_NAMES:
                self.assertTrue((user_dir / name).is_file())


if __name__ == "__main__":
    unittest.main()
