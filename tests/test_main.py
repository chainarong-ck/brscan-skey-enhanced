from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from configurator import main as configurator_main


class DefaultFrontendTests(unittest.TestCase):
    def test_reads_gtk_default(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "default-gui"
            path.write_text("gtk\n", encoding="utf-8")
            self.assertEqual(configurator_main.configured_frontend(path), "gtk")

    def test_reads_qt_default_case_insensitively(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "default-gui"
            path.write_text("Qt\n", encoding="utf-8")
            self.assertEqual(configurator_main.configured_frontend(path), "qt")

    def test_ignores_missing_or_invalid_default(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "default-gui"
            self.assertIsNone(configurator_main.configured_frontend(path))
            path.write_text("unknown\n", encoding="utf-8")
            self.assertIsNone(configurator_main.configured_frontend(path))

    def test_option_free_launch_uses_installed_default(self) -> None:
        frontend_main = Mock(return_value=17)
        with (
            patch.object(configurator_main.sys, "argv", ["brscan-skey-config"]),
            patch.object(
                configurator_main,
                "configured_frontend",
                return_value="qt",
            ),
            patch.object(
                configurator_main,
                "_load_main",
                return_value=frontend_main,
            ) as load_main,
        ):
            result = configurator_main.main()

        self.assertEqual(result, 17)
        load_main.assert_called_once_with("qt_gui")

    def test_command_option_overrides_installed_default(self) -> None:
        frontend_main = Mock(return_value=23)
        with (
            patch.object(
                configurator_main.sys,
                "argv",
                ["brscan-skey-config", "--gtk"],
            ),
            patch.object(
                configurator_main,
                "configured_frontend",
                return_value="qt",
            ),
            patch.object(
                configurator_main,
                "_load_main",
                return_value=frontend_main,
            ) as load_main,
        ):
            result = configurator_main.main()

        self.assertEqual(result, 23)
        load_main.assert_called_once_with("gtk_gui")


if __name__ == "__main__":
    unittest.main()
