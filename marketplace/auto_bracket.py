"""
Auto Bracket — Extension for SCC Editor

Automatically closes brackets, braces, parentheses, and quotes
when the opening character is typed.
"""
from extension_api import BaseExtension


_PAIRS = {
    "(": ")",
    "{": "}",
    "[": "]",
    '"': '"',
    "'": "'",
}


class AutoBracketExtension(BaseExtension):
    name = "Auto Bracket"
    version = "1.0.0"
    description = "Auto-closes (), {}, [], and quotes when you type the opener."
    author = "SCC Team"
    icon = "🔗"
    category = "Editing"
    tags = ["brackets", "auto-close", "productivity"]

    def __init__(self):
        self._binding_id = None

    def activate(self, editor):
        self._binding_id = editor.text.bind("<KeyPress>", self._on_keypress, add=True)

    def deactivate(self, editor):
        if self._binding_id:
            try:
                editor.text.unbind("<KeyPress>", self._binding_id)
            except Exception:
                pass
            self._binding_id = None

    def _on_keypress(self, event):
        ch = event.char
        if ch in _PAIRS:
            widget = event.widget
            closer = _PAIRS[ch]
            # insert closing char after cursor
            widget.after(1, lambda: self._insert_closer(widget, closer))

    @staticmethod
    def _insert_closer(widget, closer):
        try:
            widget.insert("insert", closer)
            widget.mark_set("insert", f"insert - 1 chars")
        except Exception:
            pass
