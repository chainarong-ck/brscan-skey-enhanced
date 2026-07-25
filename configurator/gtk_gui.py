#!/usr/bin/env python3
"""GTK 3 frontend for Brother scan settings."""

from __future__ import annotations

import sys

try:
    import gi

    gi.require_version("Gtk", "3.0")
    from gi.repository import Gtk
except (ImportError, ValueError) as exc:
    print(f"GTK 3 Python support is required: {exc}", file=sys.stderr)
    raise SystemExit(1)

try:
    from .config_store import (
        CONFIG_PATH,
        DEFAULT_ENHANCED_ENABLED,
        PAPER_SIZES,
        PROFILES,
        PROFILE_LABELS,
        RESOLUTIONS,
        ConfigurationError,
        ScanSettings,
        load_all,
        load_enhanced_enabled,
        restore_defaults,
        save_all,
    )
    from .user_setup import (
        UserSetupError,
        ensure_user_installation,
        set_enhanced_enabled,
    )
except ImportError:
    from config_store import (  # type: ignore
        CONFIG_PATH,
        DEFAULT_ENHANCED_ENABLED,
        PAPER_SIZES,
        PROFILES,
        PROFILE_LABELS,
        RESOLUTIONS,
        ConfigurationError,
        ScanSettings,
        load_all,
        load_enhanced_enabled,
        restore_defaults,
        save_all,
    )
    from user_setup import (  # type: ignore
        UserSetupError,
        ensure_user_installation,
        set_enhanced_enabled,
    )


class SettingsWindow(Gtk.Window):
    def __init__(self) -> None:
        super().__init__(title="Brother Scan Settings")
        self.set_border_width(18)
        self.set_default_size(560, 440)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.connect("destroy", Gtk.main_quit)
        self._changing_enabled = False
        self._enabled_state = DEFAULT_ENHANCED_ENABLED
        self.controls: dict[
            str, tuple[Gtk.ComboBoxText, Gtk.ComboBoxText, Gtk.Switch]
        ] = {}

        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        self.add(outer)

        heading = Gtk.Label()
        heading.set_markup("<big><b>Brother Scan Settings</b></big>")
        heading.set_halign(Gtk.Align.START)
        outer.pack_start(heading, False, False, 0)

        description = Gtk.Label(
            label="Choose settings for each scanner button, then click Save."
        )
        description.set_halign(Gtk.Align.START)
        outer.pack_start(description, False, False, 0)

        override_row = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL, spacing=16
        )
        override_text = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL, spacing=3
        )
        override_title = Gtk.Label()
        override_title.set_markup("<b>Use enhanced scan actions</b>")
        override_title.set_halign(Gtk.Align.START)
        override_text.pack_start(override_title, False, False, 0)
        self.override_state = Gtk.Label()
        self.override_state.set_halign(Gtk.Align.START)
        override_text.pack_start(self.override_state, False, False, 0)
        override_row.pack_start(override_text, True, True, 0)
        self.enhanced_switch = Gtk.Switch()
        self.enhanced_switch.set_valign(Gtk.Align.CENTER)
        override_row.pack_end(self.enhanced_switch, False, False, 0)
        outer.pack_start(override_row, False, False, 0)

        notebook = Gtk.Notebook()
        outer.pack_start(notebook, True, True, 0)
        for profile in PROFILES:
            notebook.append_page(
                self._build_profile_page(profile),
                Gtk.Label(label=PROFILE_LABELS[profile]),
            )

        self.status = Gtk.Label(label=f"Configuration: {CONFIG_PATH}")
        self.status.set_halign(Gtk.Align.START)
        self.status.set_ellipsize(3)
        outer.pack_start(self.status, False, False, 0)

        buttons = Gtk.ButtonBox(orientation=Gtk.Orientation.HORIZONTAL)
        buttons.set_layout(Gtk.ButtonBoxStyle.END)
        buttons.set_spacing(8)
        reset_button = Gtk.Button(label="Restore Defaults")
        reset_button.connect("clicked", self._on_restore)
        close_button = Gtk.Button(label="Close")
        close_button.connect("clicked", lambda _button: self.destroy())
        save_button = Gtk.Button(label="Save")
        save_button.get_style_context().add_class("suggested-action")
        save_button.connect("clicked", self._on_save)
        buttons.add(reset_button)
        buttons.add(close_button)
        buttons.add(save_button)
        outer.pack_start(buttons, False, False, 0)

        try:
            self._populate(load_all())
        except ConfigurationError as exc:
            self._show_error(str(exc))
            self._populate(restore_defaults())

        try:
            enabled = load_enhanced_enabled()
        except ConfigurationError as exc:
            self._show_error(str(exc))
            enabled = DEFAULT_ENHANCED_ENABLED
        self._enabled_state = enabled
        self.enhanced_switch.set_active(enabled)
        self._update_override_state(enabled)
        self.enhanced_switch.connect(
            "notify::active", self._on_enhanced_toggled
        )

    def _build_profile_page(self, profile: str) -> Gtk.Widget:
        grid = Gtk.Grid(column_spacing=18, row_spacing=18)
        grid.set_border_width(20)

        resolution = Gtk.ComboBoxText()
        for value in RESOLUTIONS:
            resolution.append(str(value), f"{value} DPI")

        paper = Gtk.ComboBoxText()
        for value in PAPER_SIZES:
            paper.append(value, value)

        duplex = Gtk.Switch()
        duplex.set_halign(Gtk.Align.START)

        for row, (label, widget) in enumerate(
            (("Resolution", resolution), ("Paper size", paper), ("Duplex", duplex))
        ):
            text = Gtk.Label(label=label)
            text.set_halign(Gtk.Align.END)
            grid.attach(text, 0, row, 1, 1)
            grid.attach(widget, 1, row, 1, 1)

        self.controls[profile] = (resolution, paper, duplex)
        return grid

    def _populate(self, settings: dict[str, ScanSettings]) -> None:
        for profile, value in settings.items():
            resolution, paper, duplex = self.controls[profile]
            resolution.set_active_id(str(value.resolution))
            paper.set_active_id(value.paper_size)
            duplex.set_active(value.duplex)

    def _collect(self) -> dict[str, ScanSettings]:
        values: dict[str, ScanSettings] = {}
        for profile, controls in self.controls.items():
            resolution, paper, duplex = controls
            values[profile] = ScanSettings(
                int(resolution.get_active_id()),
                str(paper.get_active_id()),
                duplex.get_active(),
            )
        return values

    def _on_save(self, _button: Gtk.Button) -> None:
        try:
            save_all(self._collect())
        except (ConfigurationError, TypeError, ValueError) as exc:
            self._show_error(str(exc))
            return
        self.status.set_text(f"Saved: {CONFIG_PATH}")

    def _on_enhanced_toggled(
        self, switch: Gtk.Switch, _parameter: object
    ) -> None:
        if self._changing_enabled:
            return

        enabled = switch.get_active()
        previous = self._enabled_state
        try:
            set_enhanced_enabled(enabled)
        except (ConfigurationError, UserSetupError) as exc:
            self._changing_enabled = True
            switch.set_active(previous)
            self._changing_enabled = False
            self._show_error(str(exc))
            return

        self._enabled_state = enabled
        self._update_override_state(enabled)
        state = "enabled" if enabled else "disabled"
        self.status.set_text(f"Enhanced scan actions {state}.")

    def _update_override_state(self, enabled: bool) -> None:
        if enabled:
            message = "ON — enhanced actions override Brother defaults."
        else:
            message = "OFF — Brother driver defaults are used."
        self.override_state.set_text(message)

    def _on_restore(self, _button: Gtk.Button) -> None:
        self._populate(restore_defaults())
        self.status.set_text("Defaults loaded. Click Save to apply them.")

    def _show_error(self, message: str) -> None:
        dialog = Gtk.MessageDialog(
            transient_for=self,
            modal=True,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.CLOSE,
            text="Could not update scanner settings",
        )
        dialog.format_secondary_text(message)
        dialog.run()
        dialog.destroy()


def main() -> int:
    try:
        ensure_user_installation()
    except UserSetupError as exc:
        print(f"Could not prepare user files: {exc}", file=sys.stderr)
        return 1
    window = SettingsWindow()
    window.show_all()
    Gtk.main()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
