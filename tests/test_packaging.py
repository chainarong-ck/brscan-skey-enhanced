from __future__ import annotations

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent.parent


class DebianPackageTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("dpkg-deb"), "dpkg-deb is unavailable")
    def test_debian_package_metadata_and_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "packages"
            result = subprocess.run(
                [
                    str(PROJECT_DIR / "packaging/build-deb.sh"),
                    str(output_dir),
                ],
                cwd=PROJECT_DIR,
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            packages = list(output_dir.glob("*.deb"))
            self.assertEqual(len(packages), 1)

            fields = subprocess.run(
                [
                    "dpkg-deb",
                    "--show",
                    "--showformat=${Package}\\n${Version}\\n${Architecture}\\n",
                    str(packages[0]),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            version = (PROJECT_DIR / "VERSION").read_text(
                encoding="utf-8"
            ).strip()
            self.assertEqual(
                fields.stdout,
                f"brscan-skey-enhanced\n{version}-1\nall\n",
            )

            contents = subprocess.run(
                ["dpkg-deb", "--contents", str(packages[0])],
                check=True,
                capture_output=True,
                text=True,
            ).stdout
            self.assertIn("./usr/bin/brscan-skey-config", contents)
            self.assertIn(
                "./usr/lib/brscan-skey-enhanced/default-gui",
                contents,
            )
            self.assertIn(
                "./usr/share/applications/brscan-skey-config.desktop",
                contents,
            )


if __name__ == "__main__":
    unittest.main()
