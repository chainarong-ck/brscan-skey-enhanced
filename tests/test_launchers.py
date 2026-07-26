from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent.parent


class PrefixAwareLauncherTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.stage_root = self.root / "stage"
        self.fake_bin = self.root / "bin"
        self.fake_bin.mkdir()
        self.python_log = self.root / "python.log"
        fake_python = self.fake_bin / "python3"
        fake_python.write_text(
            "#!/bin/sh\n"
            "{\n"
            "    printf 'cwd=%s\\n' \"$PWD\"\n"
            "    printf 'args'\n"
            "    printf '\\t%s' \"$@\"\n"
            "    printf '\\n'\n"
            "} > \"$PYTHON_LOG\"\n",
            encoding="utf-8",
        )
        fake_python.chmod(0o755)

        result = subprocess.run(
            [
                str(PROJECT_DIR / "packaging/install-files.sh"),
                str(self.stage_root),
                "/usr",
                "gtk",
            ],
            cwd=PROJECT_DIR,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def _environment(self) -> dict[str, str]:
        environment = os.environ.copy()
        environment.update(
            {
                "PATH": f"{self.fake_bin}:/usr/bin:/bin",
                "PYTHON_LOG": str(self.python_log),
            }
        )
        return environment

    def test_config_launcher_uses_its_own_install_prefix(self) -> None:
        launcher = self.stage_root / "usr/bin/brscan-skey-config"

        result = subprocess.run(
            [str(launcher), "--qt"],
            env=self._environment(),
            check=False,
            capture_output=True,
            text=True,
        )

        app_dir = self.stage_root / "usr/lib/brscan-skey-enhanced"
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            self.python_log.read_text(encoding="utf-8"),
            f"cwd={app_dir}\nargs\t-B\t-m\tconfigurator.main\t--qt\n",
        )

    def test_config_launcher_also_supports_usr_local_prefix(self) -> None:
        local_stage = self.root / "local-stage"
        stage_result = subprocess.run(
            [
                str(PROJECT_DIR / "packaging/install-files.sh"),
                str(local_stage),
                "/usr/local",
                "gtk",
            ],
            cwd=PROJECT_DIR,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(stage_result.returncode, 0, stage_result.stderr)

        launcher = local_stage / "usr/local/bin/brscan-skey-config"
        result = subprocess.run(
            [str(launcher), "--gtk"],
            env=self._environment(),
            check=False,
            capture_output=True,
            text=True,
        )

        app_dir = (
            local_stage / "usr/local/lib/brscan-skey-enhanced"
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            self.python_log.read_text(encoding="utf-8"),
            f"cwd={app_dir}\nargs\t-B\t-m\tconfigurator.main\t--gtk\n",
        )

    def test_settings_reader_uses_its_own_install_prefix(self) -> None:
        launcher = self.stage_root / "usr/bin/brscan-skey-read-settings"

        result = subprocess.run(
            [str(launcher), "email"],
            env=self._environment(),
            check=False,
            capture_output=True,
            text=True,
        )

        app_dir = self.stage_root / "usr/lib/brscan-skey-enhanced"
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            self.python_log.read_text(encoding="utf-8"),
            f"cwd={app_dir}\n"
            "args\t-B\t-m\tconfigurator.config_store\temail\n",
        )

    def test_config_launcher_does_not_write_python_bytecode(self) -> None:
        launcher = self.stage_root / "usr/bin/brscan-skey-config"
        environment = os.environ.copy()
        environment["PATH"] = "/usr/bin:/bin"
        environment.pop("PYTHONDONTWRITEBYTECODE", None)

        result = subprocess.run(
            [str(launcher), "--help"],
            env=environment,
            check=False,
            capture_output=True,
            text=True,
        )

        configurator_dir = (
            self.stage_root / "usr/lib/brscan-skey-enhanced/configurator"
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse((configurator_dir / "__pycache__").exists())

    def test_staged_package_has_gtk_default_and_portable_desktop_entry(
        self,
    ) -> None:
        default_gui = (
            self.stage_root
            / "usr/lib/brscan-skey-enhanced/default-gui"
        )
        desktop_entry = (
            self.stage_root
            / "usr/share/applications/brscan-skey-config.desktop"
        )

        self.assertEqual(default_gui.read_text(encoding="utf-8"), "gtk\n")
        desktop_content = desktop_entry.read_text(encoding="utf-8")
        self.assertIn("Exec=brscan-skey-config\n", desktop_content)
        self.assertIn("TryExec=brscan-skey-config\n", desktop_content)
        self.assertNotIn("/usr/local", desktop_content)

    def test_scan_script_uses_reader_from_its_own_install_prefix(
        self,
    ) -> None:
        common_script = (
            self.stage_root
            / "usr/lib/brscan-skey-enhanced/script/scan-common.sh"
        )

        result = subprocess.run(
            [
                "/bin/bash",
                "-c",
                'source "$1"; printf "%s\\n" "$BRSCAN_SETTINGS_READER"',
                "bash",
                str(common_script),
            ],
            env=self._environment(),
            check=False,
            capture_output=True,
            text=True,
        )

        expected_reader = (
            self.stage_root / "usr/bin/brscan-skey-read-settings"
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, f"{expected_reader}\n")


class PrefixAwareScanConfigTests(unittest.TestCase):
    def test_each_scan_config_accepts_an_explicit_application_directory(
        self,
    ) -> None:
        actions = {
            "scantofile.config": "brother-scan-to-file.sh",
            "scantoemail.config": "brother-scan-to-email.sh",
            "scantoimage.config": "brother-scan-to-image.sh",
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            app_dir = Path(temp_dir) / "app"
            script_dir = app_dir / "script"
            script_dir.mkdir(parents=True)
            environment = os.environ.copy()
            environment["BRSCAN_APP_DIR"] = str(app_dir)

            for config_name, script_name in actions.items():
                action = script_dir / script_name
                action.write_text(
                    "#!/bin/sh\nprintf '%s\\n' \"$1\"\n",
                    encoding="utf-8",
                )
                action.chmod(0o755)

                result = subprocess.run(
                    ["/bin/bash", str(PROJECT_DIR / config_name), "device"],
                    env=environment,
                    check=False,
                    capture_output=True,
                    text=True,
                )

                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout, "device\n")

    def test_stale_user_overrides_remove_themselves(self) -> None:
        config_names = (
            "scantofile.config",
            "scantoemail.config",
            "scantoimage.config",
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            home = Path(temp_dir)
            user_dir = home / ".brscan-skey"
            user_dir.mkdir()
            environment = os.environ.copy()
            environment["HOME"] = str(home)
            environment["BRSCAN_APP_DIR"] = str(home / "missing-app")

            for config_name in config_names:
                override = user_dir / config_name
                override.write_text(
                    (PROJECT_DIR / config_name).read_text(encoding="utf-8"),
                    encoding="utf-8",
                )

                result = subprocess.run(
                    [
                        "/bin/bash",
                        "-c",
                        "set -u; source \"$1\"; "
                        "printf 'driver-default:%s:%s:%s\\n' "
                        '"$resolution" "$size" "$duplex"',
                        "bash",
                        str(override),
                    ],
                    env=environment,
                    check=False,
                    capture_output=True,
                    text=True,
                )

                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(
                    result.stdout,
                    "driver-default:100:A4:OFF\n",
                )
                self.assertFalse(override.exists())


if __name__ == "__main__":
    unittest.main()
