from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent.parent


class InstallScriptTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.bin_dir = self.root / "bin"
        self.command_log = self.root / "commands.log"
        self.bin_dir.mkdir()
        self._write_executable(
            "id",
            "#!/bin/sh\n"
            "if [ \"${1:-}\" = -u ]; then\n"
            "    printf '0\\n'\n"
            "    exit 0\n"
            "fi\n"
            "exec /usr/bin/id \"$@\"\n",
        )
        self._write_executable("python3", "#!/bin/sh\nexit 0\n")
        self._write_executable("magick", "#!/bin/sh\nexit 0\n")
        self._write_executable(
            "install",
            "#!/bin/bash\n"
            "{\n"
            "    printf 'install'\n"
            "    read_stdin=false\n"
            "    for argument in \"$@\"; do\n"
            "        printf '\\t%s' \"$argument\"\n"
            "        if [ \"$argument\" = /dev/stdin ]; then\n"
            "            read_stdin=true\n"
            "        fi\n"
            "    done\n"
            "    if $read_stdin; then\n"
            "        IFS= read -r value\n"
            "        printf '\\tstdin=%s' \"$value\"\n"
            "    fi\n"
            "    printf '\\n'\n"
            "} >> \"$COMMAND_LOG\"\n",
        )
        self._write_executable(
            "rm",
            "#!/bin/bash\n"
            "{\n"
            "    printf 'rm'\n"
            "    printf '\\t%s' \"$@\"\n"
            "    printf '\\n'\n"
            "} >> \"$COMMAND_LOG\"\n",
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def _write_executable(self, name: str, content: str) -> None:
        path = self.bin_dir / name
        path.write_text(content, encoding="utf-8")
        path.chmod(0o755)

    def _environment(self) -> dict[str, str]:
        environment = os.environ.copy()
        environment.update(
            {
                "COMMAND_LOG": str(self.command_log),
                "PATH": f"{self.bin_dir}:/usr/bin:/bin",
            }
        )
        return environment

    def _run(
        self, script: str, *arguments: str, input_text: str | None = None
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["/bin/bash", str(PROJECT_DIR / script), *arguments],
            cwd=PROJECT_DIR,
            env=self._environment(),
            input=input_text,
            check=False,
            capture_output=True,
            text=True,
        )

    def test_installer_uses_gtk_when_prompt_is_accepted(self) -> None:
        result = self._run("install.sh", input_text="\n")

        self.assertEqual(result.returncode, 0, result.stderr)
        commands = self.command_log.read_text(encoding="utf-8")
        self.assertIn(
            "/usr/local/lib/brscan-skey-enhanced/default-gui"
            "\tstdin=gtk",
            commands,
        )
        self.assertNotIn("settings.ini.example", commands)
        self.assertNotIn("load-scan-settings.sh", commands)
        self.assertIn(
            "rm\t-rf\t--\t/usr/local/lib/brscan-skey-enhanced",
            commands,
        )

    def test_installer_accepts_qt_without_prompt(self) -> None:
        result = self._run("install.sh", "--gui", "qt")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("Selection [1]", result.stdout)
        commands = self.command_log.read_text(encoding="utf-8")
        self.assertIn(
            "/usr/local/lib/brscan-skey-enhanced/default-gui"
            "\tstdin=qt",
            commands,
        )

    def test_uninstaller_targets_only_system_wide_files(self) -> None:
        result = self._run("uninstall.sh")

        self.assertEqual(result.returncode, 0, result.stderr)
        commands = self.command_log.read_text(encoding="utf-8")
        self.assertIn("/usr/local/bin/brscan-skey-config", commands)
        self.assertIn("/usr/local/bin/brscan-skey-read-settings", commands)
        self.assertIn(
            "/usr/local/share/applications/brscan-skey-config.desktop",
            commands,
        )
        self.assertIn("/usr/local/lib/brscan-skey-enhanced", commands)
        self.assertNotIn(".brscan-skey", commands)


if __name__ == "__main__":
    unittest.main()
