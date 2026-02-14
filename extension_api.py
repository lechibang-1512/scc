"""
extension_api.py

Defines the base class for all editor extensions.
Every extension .py file placed in the extensions/ directory must define
a class that inherits from BaseExtension.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    import tkinter as tk

# Settings are stored per-extension under extensions/settings/
_SETTINGS_DIR = Path(__file__).parent / "extensions" / "settings"


class BaseExtension:
    """Abstract base class for editor extensions.

    Subclasses MUST set the class-level metadata attributes and override
    ``activate`` / ``deactivate`` at minimum.
    """

    # ── Metadata (override in subclass) ──────────────────────────────
    name: str = "Unnamed Extension"
    version: str = "0.1.0"
    description: str = ""
    author: str = "Unknown"
    icon: str = "🧩"  # emoji or single char used as visual badge
    category: str = "Other"  # Appearance | Editing | Tools | Languages | Other
    tags: List[str] = []

    # ── Internal state ───────────────────────────────────────────────
    _keybindings: Dict[str, str] = {}  # key_sequence -> binding_id
    _settings_cache: Dict[str, Any] = {}

    # ── Lifecycle ────────────────────────────────────────────────────
    def activate(self, editor: Any) -> None:
        """Called when the extension is activated.

        *editor* is the ``CppEditorApp`` instance – extensions can use it
        to manipulate the text widget, menus, status bar, etc.
        """

    def deactivate(self, editor: Any) -> None:
        """Called when the extension is deactivated / uninstalled.

        Extensions should clean up any UI modifications here.
        Keybindings registered via ``register_keybinding`` are automatically
        removed — no need to call ``unregister_keybinding`` manually.
        """

    def on_shutdown(self, editor: Any) -> None:
        """Called once when the application is closing (after ``deactivate``).

        Override this to persist state, flush logs, close network connections,
        or perform any final cleanup that should only happen at app exit.
        Unlike ``deactivate``, this is *not* called on disable/uninstall.
        """

    # ── Event hooks (optional overrides) ─────────────────────────────
    def on_key(self, editor: Any, event: "tk.Event") -> Optional[str]:
        """Called on every key-release in the text widget.

        Return ``"break"`` to swallow the event, or ``None`` to let it
        propagate normally.
        """
        return None

    def on_file_open(self, editor: Any, path: str) -> None:
        """Called after a file is opened."""

    def on_file_save(self, editor: Any, path: str) -> None:
        """Called after a file is saved."""

    def on_build_start(self, editor: Any) -> None:
        """Called just before compilation begins."""

    def on_build_end(self, editor: Any, success: bool) -> None:
        """Called after compilation finishes."""

    def contribute_menu(self, editor: Any, menubar: "tk.Menu") -> None:
        """Called once during activation so the extension can add menus."""

    # ── Settings ─────────────────────────────────────────────────────
    def default_settings(self) -> Dict[str, Any]:
        """Override to declare configurable settings with defaults.

        Example::

            def default_settings(self):
                return {"backup_dir": "~/.backups", "max_backups": 5}
        """
        return {}

    def get_setting(self, key: str) -> Any:
        """Read a persisted setting value (falls back to default)."""
        if not self._settings_cache:
            self._settings_cache = self._load_settings()
        defaults = self.default_settings()
        return self._settings_cache.get(key, defaults.get(key))

    def set_setting(self, key: str, value: Any) -> None:
        """Persist a setting value."""
        if not self._settings_cache:
            self._settings_cache = self._load_settings()
        self._settings_cache[key] = value
        self._save_settings()

    def _settings_path(self) -> Path:
        _SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
        safe_name = self.__class__.__name__.lower()
        return _SETTINGS_DIR / f"{safe_name}.json"

    def _load_settings(self) -> Dict[str, Any]:
        p = self._settings_path()
        if p.exists():
            try:
                return json.loads(p.read_text())
            except Exception:
                pass
        return dict(self.default_settings())

    def _save_settings(self) -> None:
        p = self._settings_path()
        try:
            p.write_text(json.dumps(self._settings_cache, indent=2))
        except Exception:
            pass

    # ── Keybinding helpers ───────────────────────────────────────────
    def register_keybinding(
        self, editor: Any, key_sequence: str, callback
    ) -> None:
        """Bind *key_sequence* (e.g. ``"<Control-Shift-P>"``) to *callback*.

        The binding is automatically removed on ``deactivate``.
        """
        bid = editor.text.bind(key_sequence, callback, add=True)
        self._keybindings[key_sequence] = bid

    def unregister_keybinding(self, editor: Any, key_sequence: str) -> None:
        """Remove a previously registered keybinding."""
        bid = self._keybindings.pop(key_sequence, None)
        if bid:
            try:
                editor.text.unbind(key_sequence, bid)
            except Exception:
                pass

    def unregister_all_keybindings(self, editor: Any) -> None:
        """Remove all keybindings registered by this extension."""
        for key_seq in list(self._keybindings):
            self.unregister_keybinding(editor, key_seq)

    # ── Notification helper ──────────────────────────────────────────
    @staticmethod
    def show_notification(
        editor: Any, message: str, duration_ms: int = 3000
    ) -> None:
        """Show a transient notification toast at the bottom-right."""
        if hasattr(editor, "_show_toast"):
            editor._show_toast(message, duration_ms)

    # ── Convenience helpers ──────────────────────────────────────────
    @staticmethod
    def get_text(editor: Any) -> str:
        """Return the full editor text content."""
        return editor.text.get("1.0", "end-1c")

    @staticmethod
    def set_status(editor: Any, msg: str) -> None:
        """Update the status bar."""
        editor.status_var.set(msg)
