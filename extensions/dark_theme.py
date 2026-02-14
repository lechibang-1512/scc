"""
Dark Theme — Extension for SCC Editor

Switches the entire editor UI to a sleek dark colour scheme and adds
a menu item to toggle it on/off.
"""
import tkinter as tk
from extension_api import BaseExtension


_DARK = {
    "bg":         "#1e1e2e",
    "fg":         "#cdd6f4",
    "insert_bg":  "#f5e0dc",
    "line_bg":    "#181825",
    "line_fg":    "#6c7086",
    "output_bg":  "#11111b",
    "output_fg":  "#a6adc8",
    "status_bg":  "#181825",
    "status_fg":  "#89b4fa",
    "select_bg":  "#45475a",
}

_LIGHT = {
    "bg":         "#ffffff",
    "fg":         "#000000",
    "insert_bg":  "black",
    "line_bg":    "#f0f0f0",
    "line_fg":    "gray",
    "output_bg":  "#111111",
    "output_fg":  "#ffffff",
    "status_bg":  "SystemButtonFace",
    "status_fg":  "black",
    "select_bg":  "#c0c0ff",
}


class DarkThemeExtension(BaseExtension):
    name = "Dark Theme"
    version = "1.0.0"
    description = "Toggle a beautiful dark colour scheme for the editor."
    author = "SCC Team"
    icon = "🌙"
    category = "Appearance"
    tags = ["theme", "dark mode", "colors"]

    def __init__(self):
        self._menu: tk.Menu | None = None
        self._dark_active = False

    def activate(self, editor):
        self._apply(editor, _DARK)
        self._dark_active = True

    def deactivate(self, editor):
        self._apply(editor, _LIGHT)
        self._dark_active = False
        # Remove the Theme cascade from the menubar
        if self._menu and hasattr(self, '_menubar') and self._menubar:
            try:
                # Find and delete the "Theme" cascade entry
                last = self._menubar.index("end")
                if last is not None:
                    for i in range(int(last), -1, -1):
                        try:
                            label = self._menubar.entrycget(i, "label")
                            if label == "Theme":
                                self._menubar.delete(i)
                                break
                        except Exception:
                            pass
            except Exception:
                pass
            self._menu = None
            self._menubar = None

    def contribute_menu(self, editor, menubar):
        # menubar is the actual tk.Menu widget
        import tkinter as tk
        self._menu = tk.Menu(menubar, tearoff=False)
        self._menu.add_command(
            label="Toggle Dark/Light",
            command=lambda: self._toggle(editor),
        )
        menubar.add_cascade(label="Theme", menu=self._menu)
        self._menubar = menubar

    def _toggle(self, editor):
        if self._dark_active:
            self._apply(editor, _LIGHT)
            self._dark_active = False
        else:
            self._apply(editor, _DARK)
            self._dark_active = True

    @staticmethod
    def _apply(editor, scheme):
        try:
            editor.text.config(
                bg=scheme["bg"], fg=scheme["fg"],
                insertbackground=scheme["insert_bg"],
                selectbackground=scheme["select_bg"],
            )
            editor.line_numbers.config(bg=scheme["line_bg"], fg=scheme["line_fg"])
            editor.output.config(bg=scheme["output_bg"], fg=scheme["output_fg"])
            # status bar — find by status_var
            for w in editor.root.pack_slaves():
                if isinstance(w, tk.Label):
                    try:
                        if str(w.cget("textvariable")) == str(editor.status_var):
                            w.config(bg=scheme["status_bg"], fg=scheme["status_fg"])
                    except Exception:
                        pass
        except Exception:
            pass
