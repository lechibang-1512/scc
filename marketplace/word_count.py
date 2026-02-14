"""
Word Count — Extension for SCC Editor

Displays a live word / line / character count in the status bar area.
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
        self._label = None
        self._after_id = None

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
        self._schedule(editor)

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

    def _schedule(self, editor):
        self._update(editor)
        self._after_id = editor.root.after(800, lambda: self._schedule(editor))

    def _update(self, editor):
        try:
            text = self.get_text(editor)
            words = len(text.split())
            lines = text.count("\n") + (1 if text else 0)
            chars = len(text)
            if self._label:
                self._label.config(text=f"Words: {words}  |  Lines: {lines}  |  Chars: {chars}")
        except Exception:
            pass
