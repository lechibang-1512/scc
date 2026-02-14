"""
Line Highlight — Extension for SCC Editor

Highlights the current line (where the cursor is) with a subtle
background colour that follows the cursor in real-time.
"""
import tkinter as tk
from extension_api import BaseExtension


class LineHighlightExtension(BaseExtension):
    name = "Line Highlight"
    version = "1.0.0"
    description = "Highlights the current cursor line with a subtle background colour."
    author = "SCC Team"
    icon = "🔦"
    category = "Appearance"
    tags = ["cursor", "highlight", "line"]

    def __init__(self):
        super().__init__()
        self._bindings = []
        self._after_id = None
        self._last_line = None  # avoid redundant updates

    def activate(self, editor):
        tag = "ext_curline"
        editor.text.tag_configure(tag, background="#2a2a3d")
        editor.text.tag_lower(tag)  # below syntax tags

        # bind cursor movement events
        events = ("<KeyRelease>", "<Button-1>", "<ButtonRelease-1>")
        for ev in events:
            bid = editor.text.bind(ev, lambda e: self._debounced_update(editor), add=True)
            self._bindings.append((ev, bid))

        self._update(editor)

    def deactivate(self, editor):
        for ev, bid in self._bindings:
            try:
                editor.text.unbind(ev, bid)
            except Exception:
                pass
        self._bindings.clear()
        try:
            editor.text.tag_remove("ext_curline", "1.0", "end")
            editor.text.tag_delete("ext_curline")
        except Exception:
            pass
        if self._after_id:
            try:
                editor.root.after_cancel(self._after_id)
            except Exception:
                pass
            self._after_id = None
        self._last_line = None

    def _debounced_update(self, editor):
        """Debounce rapid cursor movements (50ms)."""
        if self._after_id:
            try:
                editor.root.after_cancel(self._after_id)
            except Exception:
                pass
        self._after_id = editor.root.after(50, lambda: self._update(editor))

    def _update(self, editor):
        self._after_id = None
        try:
            line = editor.text.index("insert").split(".")[0]
            # Skip if cursor hasn't moved to a different line
            if line == self._last_line:
                return
            self._last_line = line
            editor.text.tag_remove("ext_curline", "1.0", "end")
            editor.text.tag_add("ext_curline", f"{line}.0", f"{line}.0 lineend +1c")
        except Exception:
            pass
