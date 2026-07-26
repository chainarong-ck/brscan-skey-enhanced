from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent.parent
SCRIPT_DIR = PROJECT_DIR / "script"


class ScanScriptTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.bin_dir = self.root / "bin"
        self.output_dir = self.root / "output"
        self.bin_dir.mkdir()
        self.scanner = self.bin_dir / "fake-scanner"
        self.reader = self.bin_dir / "fake-settings-reader"
        self.scanner_log = self.root / "scanner-arguments"
        self.email_log = self.root / "email-arguments"
        self._write_executable(
            self.scanner,
            "#!/bin/bash\n"
            "printf '%s\\n' \"$@\" > \"$SCANNER_LOG\"\n"
            "output=''\n"
            "while [ \"$#\" -gt 0 ]; do\n"
            "    if [ \"$1\" = --outputfile ]; then\n"
            "        output=\"$2\"\n"
            "        shift 2\n"
            "    else\n"
            "        shift\n"
            "    fi\n"
            "done\n"
            "printf 'TIFF data\\n' > \"$output\"\n",
        )
        self._write_executable(
            self.reader,
            "#!/bin/sh\nprintf '200\\nA4\\nOFF\\n'\n",
        )
        self._write_executable(
            self.bin_dir / "magick",
            "#!/bin/bash\noutput=\"${!#}\"\ncp -- \"$1\" \"$output\"\n",
        )
        self._write_executable(
            self.bin_dir / "xdg-email",
            "#!/bin/bash\nprintf '%s\\n' \"$@\" > \"$EMAIL_LOG\"\n",
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    @staticmethod
    def _write_executable(path: Path, content: str) -> None:
        path.write_text(content, encoding="utf-8")
        path.chmod(0o755)

    def _environment(self) -> dict[str, str]:
        environment = os.environ.copy()
        environment.update(
            {
                "HOME": str(self.root),
                "PATH": f"{self.bin_dir}:/usr/bin:/bin",
                "BRSCAN_SCANNER": str(self.scanner),
                "BRSCAN_SETTINGS_READER": str(self.reader),
                "BRSCAN_OUTPUT_DIR": str(self.output_dir),
                "EMAIL_LOG": str(self.email_log),
                "SCANNER_LOG": str(self.scanner_log),
            }
        )
        environment.pop("DISPLAY", None)
        environment.pop("WAYLAND_DISPLAY", None)
        return environment

    def _run(
        self, script_name: str, device: str = "test-device"
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [str(SCRIPT_DIR / script_name), device],
            env=self._environment(),
            check=False,
            capture_output=True,
            text=True,
        )

    def test_scan_to_file_creates_pdf(self) -> None:
        result = self._run("brother-scan-to-file.sh")

        self.assertEqual(result.returncode, 0, result.stderr)
        outputs = list(self.output_dir.glob("brscan_file_*.pdf"))
        self.assertEqual(len(outputs), 1)
        self.assertEqual(outputs[0].read_text(encoding="utf-8"), "TIFF data\n")
        self.assertEqual(outputs[0].stat().st_mode & 0o077, 0)
        self.assertEqual(self.output_dir.stat().st_mode & 0o077, 0)
        self.assertEqual(list(self.output_dir.glob("*.tif")), [])

    def test_scan_to_image_creates_jpeg(self) -> None:
        result = self._run("brother-scan-to-image.sh")

        self.assertEqual(result.returncode, 0, result.stderr)
        outputs = list(self.output_dir.glob("brscan_image_*.jpg"))
        self.assertEqual(len(outputs), 1)

    def test_duplex_settings_are_passed_to_the_brother_scanner(self) -> None:
        self._write_executable(
            self.reader,
            "#!/bin/sh\nprintf '600\\nLegal\\nON\\n'\n",
        )

        result = self._run("brother-scan-to-file.sh")

        self.assertEqual(result.returncode, 0, result.stderr)
        arguments = self.scanner_log.read_text(encoding="utf-8").splitlines()
        self.assertIn("600", arguments)
        self.assertIn("Legal", arguments)
        self.assertIn("ADF_C", arguments)
        self.assertIn("--duplex", arguments)

    def test_scan_to_email_attaches_pdf(self) -> None:
        result = self._run("brother-scan-to-email.sh")

        self.assertEqual(result.returncode, 0, result.stderr)
        arguments = self.email_log.read_text(encoding="utf-8")
        self.assertIn("--attach\n", arguments)
        self.assertIn("brscan_email_", arguments)

    def test_conversion_failure_preserves_tiff(self) -> None:
        self._write_executable(
            self.bin_dir / "magick",
            "#!/bin/bash\n"
            "output=\"${!#}\"\n"
            "printf 'partial\\n' > \"$output\"\n"
            "exit 1\n",
        )

        result = self._run("brother-scan-to-file.sh")

        self.assertEqual(result.returncode, 1)
        self.assertEqual(
            len(list(self.output_dir.glob("brscan_file_*.tif"))),
            1,
        )
        self.assertEqual(list(self.output_dir.glob("*.pdf")), [])

    def test_missing_scanner_device_is_rejected(self) -> None:
        result = self._run("brother-scan-to-file.sh", "")

        self.assertEqual(result.returncode, 1)
        self.assertIn("scanner device name is missing", result.stderr)
        self.assertFalse(self.output_dir.exists())


if __name__ == "__main__":
    unittest.main()
