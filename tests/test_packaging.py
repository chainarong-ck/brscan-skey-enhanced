from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent.parent


class PackageTests(unittest.TestCase):
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
            self.assertIn(
                "./usr/share/doc/brscan-skey-enhanced/LICENSE",
                contents,
            )

            control_dir = Path(temp_dir) / "control"
            subprocess.run(
                [
                    "dpkg-deb",
                    "--control",
                    str(packages[0]),
                    str(control_dir),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            postrm = control_dir / "postrm"
            self.assertTrue(postrm.stat().st_mode & 0o111)
            self.assertIn(
                "/usr/lib/brscan-skey-enhanced/configurator/__pycache__",
                postrm.read_text(encoding="utf-8"),
            )

    def test_rpm_postun_cleans_python_bytecode(self) -> None:
        spec = (
            PROJECT_DIR / "packaging/brscan-skey-enhanced.spec"
        ).read_text(encoding="utf-8")

        self.assertIn("%postun", spec)
        self.assertIn(
            "%{_prefix}/lib/%{name}/configurator/__pycache__",
            spec,
        )
        self.assertIn("License:        MIT", spec)
        self.assertNotIn("LicenseRef-Unknown", spec)

    def test_arch_package_metadata_matches_release(self) -> None:
        pkgbuild = (
            PROJECT_DIR / "packaging/arch/PKGBUILD"
        ).read_text(encoding="utf-8")
        version = (PROJECT_DIR / "VERSION").read_text(
            encoding="utf-8"
        ).strip()

        self.assertIn(f"pkgver={version}\n", pkgbuild)
        self.assertIn("arch=('any')", pkgbuild)
        self.assertIn("license=('MIT')", pkgbuild)
        self.assertIn("'python>=3.9'", pkgbuild)
        self.assertIn("'python-gobject'", pkgbuild)
        self.assertIn("'imagemagick:", pkgbuild)
        self.assertIn(
            '"${pkgdir}/usr/share/licenses/${pkgname}/LICENSE"',
            pkgbuild,
        )

    def test_arch_package_builder_renders_checksum_and_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            version = (PROJECT_DIR / "VERSION").read_text(
                encoding="utf-8"
            ).strip()
            fake_bin = root / "bin"
            output_dir = root / "output"
            fake_bin.mkdir()
            fake_makepkg = fake_bin / "makepkg"
            fake_makepkg.write_text(
                "#!/bin/bash\n"
                "set -eu\n"
                "if grep -q \"sha256sums=('SKIP')\" PKGBUILD; then\n"
                "    echo 'source checksum was not rendered' >&2\n"
                "    exit 1\n"
                "fi\n"
                "source PKGBUILD\n"
                "archive=\"${pkgname}-${pkgver}.tar.gz\"\n"
                "test -f \"$archive\"\n"
                "tar -tzf \"$archive\" | "
                "grep -q \"${pkgname}-${pkgver}/LICENSE\"\n"
                "touch \"$PKGDEST/"
                "${pkgname}-${pkgver}-${pkgrel}-any.pkg.tar.zst\"\n",
                encoding="utf-8",
            )
            fake_makepkg.chmod(0o755)
            environment = os.environ.copy()
            environment["PATH"] = (
                f"{fake_bin}:{environment.get('PATH', '')}"
            )

            result = subprocess.run(
                [
                    str(PROJECT_DIR / "packaging/build-arch.sh"),
                    str(output_dir),
                ],
                cwd=PROJECT_DIR,
                env=environment,
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            packages = list(output_dir.glob("*.pkg.tar.zst"))
            self.assertEqual(len(packages), 1)
            self.assertEqual(
                packages[0].name,
                f"brscan-skey-enhanced-{version}-1-any.pkg.tar.zst",
            )

    def test_arch_ci_builds_and_installs_native_package(self) -> None:
        workflow = (
            PROJECT_DIR / ".github/workflows/test.yml"
        ).read_text(encoding="utf-8")

        self.assertIn("package_format: arch", workflow)
        self.assertIn("./packaging/build-arch.sh", workflow)
        self.assertIn("pacman -Qip dist/*.pkg.tar.zst", workflow)
        self.assertIn(
            "pacman -U --noconfirm ./dist/*.pkg.tar.zst",
            workflow,
        )
        self.assertNotIn("package_format: none", workflow)


if __name__ == "__main__":
    unittest.main()
