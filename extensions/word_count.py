"""
Word Count — Extension for SCC Editor

Displays a live word / line / character count in the status bar area.
Uses event-driven updates instead of continuous polling.
"""
from extension_api import BaseExtension


class WordCountExtension(BaseExtension):
    name = "Word Count"
    version = "1.0.0"
    description = "Shows live word, line, and character count in a status label."
    author = "SCC Team"
    icon = "📊"
    category = "Tools"
    tags = ["word count", "statistics", "status bar"]

    def __init__(self):
        super().__init__()
        self._label = None
        self._after_id = None
        self._editor = None

    def activate(self, editor):
        import tkinter as tk
        self._label = tk.Label(
            editor.root,
            text="Words: 0 | Lines: 0 | Chars: 0",
            bg="#1e1e2e", fg="#89b4fa",
            font=("Consolas", 10), anchor="e", padx=8,
        )
        self._label.pack(side="bottom", fill="x")
        self._editor = editor
        # Do initial update
        self._update(editor)

    def deactivate(self, editor):
        if self._after_id:
            try:
                editor.root.after_cancel(self._after_id)
            except Exception:
                pass
            self._after_id = None
        if self._label:
            self._label.destroy()
            self._label = None
        self._editor = None

    def on_key(self, editor, event):
        """Update word count on key events with debounce."""
        if self._after_id:
            try:
                editor.root.after_cancel(self._after_id)
            except Exception:
                pass
        self._after_id = editor.root.after(500, lambda: self._update(editor))
        return None

    def on_file_open(self, editor, path):
        """Update immediately when a file is opened."""
        self._update(editor)

    def _update(self, editor):
        self._after_id = None
        try:
            text = self.get_text(editor)
            words = len(text.split())
            lines = text.count("\n") + (1 if text else 0)
            chars = len(text)
            if self._label:
                self._label.config(text=f"Words: {words}  |  Lines: {lines}  |  Chars: {chars}")
        except Exception:
            pass
