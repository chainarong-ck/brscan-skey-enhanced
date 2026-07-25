#!/usr/bin/env python3
"""Qt frontend for Brother scan settings (PySide6 or PyQt6)."""

from __future__ import annotations

import sys

QT_API = ""
try:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import (
        QApplication,
        QCheckBox,
        QComboBox,
        QDialog,
        QDialogButtonBox,
        QFormLayout,
        QLabel,
        QMessageBox,
        QPushButton,
        QTabWidget,
        QVBoxLayout,
        QWidget,
    )

    QT_API = "PySide6"
except ImportError:
    try:
        from PyQt6.QtCore import Qt
        from PyQt6.QtWidgets import (
            QApplication,
            QCheckBox,
            QComboBox,
            QDialog,
            QDialogButtonBox,
            QFormLayout,
            QLabel,
            QMessageBox,
            QPushButton,
            QTabWidget,
            QVBoxLayout,
            QWidget,
        )

        QT_API = "PyQt6"
    except ImportError:
        print(
            "Qt GUI requires PySide6 or PyQt6. "
            "The GTK GUI is available at configurator/gtk_gui.py.",
            file=sys.stderr,
        )
        raise SystemExit(1)

try:
    from .config_store import (
        CONFIG_PATH,
        PAPER_SIZES,
        PROFILES,
        PROFILE_LABELS,
        RESOLUTIONS,
        ConfigurationError,
        ScanSettings,
        load_all,
        restore_defaults,
        save_all,
    )
except ImportError:
    from config_store import (  # type: ignore
        CONFIG_PATH,
        PAPER_SIZES,
        PROFILES,
        PROFILE_LABELS,
        RESOLUTIONS,
        ConfigurationError,
        ScanSettings,
        load_all,
        restore_defaults,
        save_all,
    )


class SettingsDialog(QDialog):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Brother Scan Settings")
        self.resize(520, 350)
        self.controls: dict[str, tuple[QComboBox, QComboBox, QCheckBox]] = {}

        layout = QVBoxLayout(self)
        heading = QLabel("<h2>Brother Scan Settings</h2>")
        layout.addWidget(heading)
        layout.addWidget(
            QLabel("Choose settings for each scanner button, then click Save.")
        )

        tabs = QTabWidget()
        layout.addWidget(tabs)
        for profile in PROFILES:
            page = QWidget()
            form = QFormLayout(page)
            resolution = QComboBox()
            for value in RESOLUTIONS:
                resolution.addItem(f"{value} DPI", value)
            paper = QComboBox()
            paper.addItems(PAPER_SIZES)
            duplex = QCheckBox("Use automatic document feeder")
            form.addRow("Resolution", resolution)
            form.addRow("Paper size", paper)
            form.addRow("Duplex", duplex)
            self.controls[profile] = (resolution, paper, duplex)
            tabs.addTab(page, PROFILE_LABELS[profile])

        self.status = QLabel(f"Configuration: {CONFIG_PATH}")
        self.status.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        layout.addWidget(self.status)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Close
            | QDialogButtonBox.StandardButton.RestoreDefaults
        )
        save_button = buttons.button(QDialogButtonBox.StandardButton.Save)
        close_button = buttons.button(QDialogButtonBox.StandardButton.Close)
        reset_button = buttons.button(
            QDialogButtonBox.StandardButton.RestoreDefaults
        )
        save_button.clicked.connect(self._save)
        close_button.clicked.connect(self.reject)
        reset_button.clicked.connect(self._restore)
        layout.addWidget(buttons)

        try:
            self._populate(load_all())
        except ConfigurationError as exc:
            self._error(str(exc))
            self._populate(restore_defaults())

    def _populate(self, settings: dict[str, ScanSettings]) -> None:
        for profile, value in settings.items():
            resolution, paper, duplex = self.controls[profile]
            resolution.setCurrentIndex(resolution.findData(value.resolution))
            paper.setCurrentText(value.paper_size)
            duplex.setChecked(value.duplex)

    def _collect(self) -> dict[str, ScanSettings]:
        return {
            profile: ScanSettings(
                int(resolution.currentData()),
                paper.currentText(),
                duplex.isChecked(),
            )
            for profile, (resolution, paper, duplex) in self.controls.items()
        }

    def _save(self) -> None:
        try:
            save_all(self._collect())
        except ConfigurationError as exc:
            self._error(str(exc))
            return
        self.status.setText(f"Saved: {CONFIG_PATH}")

    def _restore(self) -> None:
        self._populate(restore_defaults())
        self.status.setText("Defaults loaded. Click Save to apply them.")

    def _error(self, message: str) -> None:
        QMessageBox.critical(
            self, "Brother Scan Settings", f"Could not update settings:\n{message}"
        )


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Brother Scan Settings")
    dialog = SettingsDialog()
    dialog.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
