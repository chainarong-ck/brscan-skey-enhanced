"""Select and launch an installed Brother scan settings frontend."""

from __future__ import annotations

import argparse
import importlib
import importlib.util
import sys
from pathlib import Path


DEFAULT_FRONTEND_PATH = Path(__file__).resolve().parent.parent / "default-gui"


def _module_available(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def _gtk_available() -> bool:
    try:
        import gi

        gi.require_version("Gtk", "3.0")
        from gi.repository import Gtk  # noqa: F401
    except (ImportError, ValueError):
        return False
    return True


def _load_main(module_name: str):
    module = importlib.import_module(f".{module_name}", package=__package__)
    return module.main


def configured_frontend(
    path: Path = DEFAULT_FRONTEND_PATH,
) -> str | None:
    try:
        frontend = path.read_text(encoding="utf-8").strip().lower()
    except OSError:
        return None
    return frontend if frontend in {"gtk", "qt"} else None


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Configure Brother brscan-skey scan profiles."
    )
    frontend = parser.add_mutually_exclusive_group()
    frontend.add_argument(
        "--gtk", action="store_true", help="use the GTK 3 frontend"
    )
    frontend.add_argument(
        "--qt", action="store_true", help="use the Qt 6 frontend"
    )
    args = parser.parse_args()
    sys.argv = [sys.argv[0]]

    if args.gtk:
        return _load_main("gtk_gui")()
    if args.qt:
        return _load_main("qt_gui")()

    default_frontend = configured_frontend()
    if default_frontend == "gtk":
        return _load_main("gtk_gui")()
    if default_frontend == "qt":
        return _load_main("qt_gui")()

    if _gtk_available():
        return _load_main("gtk_gui")()
    if _module_available("PySide6") or _module_available("PyQt6"):
        return _load_main("qt_gui")()

    print(
        "No supported GUI toolkit was found. Install GTK 3 with PyGObject "
        "(recommended), PySide6, or PyQt6.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
