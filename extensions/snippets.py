"""
Snippets — Extension for SCC Editor

Type a trigger word and press Tab to expand into a code template.
Supports C++ snippets: forr, main, cls, iff, cout, inc, whl, sw
"""
from extension_api import BaseExtension

_SNIPPETS = {
    "forr": "for (int i = 0; i < n; i++) {\n    \n}",
    "main": '#include <iostream>\nusing namespace std;\n\nint main() {\n    \n    return 0;\n}',
    "cls": "class ClassName {\npublic:\n    ClassName() {}\n    ~ClassName() {}\n\nprivate:\n    \n};",
    "iff": "if (condition) {\n    \n} else {\n    \n}",
    "cout": 'cout << "" << endl;',
    "inc": "#include <>",
    "whl": "while (condition) {\n    \n}",
    "sw": "switch (variable) {\n    case 1:\n        break;\n    default:\n        break;\n}",
}


class SnippetsExtension(BaseExtension):
    name = "Code Snippets"
    version = "1.0.0"
    description = "Tab-expand trigger words into C++ code templates (forr, main, cls, iff, cout, inc, whl, sw)."
    author = "SCC Team"
    icon = "✂️"
    category = "Editing"
    tags = ["snippets", "templates", "productivity"]

    def __init__(self):
        super().__init__()

    def activate(self, editor):
        self.register_keybinding(editor, "<Tab>", lambda e: self._on_tab(editor, e))
        self.show_notification(editor, "Snippets active — type a trigger + Tab")

    def deactivate(self, editor):
        pass  # keybindings auto-cleaned

    def _on_tab(self, editor, event):
        widget = editor.text
        try:
            cursor = widget.index("insert")
            line_start = widget.index(f"{cursor} linestart")
            line_text = widget.get(line_start, cursor)
            # Extract last word (fast reverse scan)
            word = ""
            for ch in reversed(line_text):
                if ch.isalnum() or ch == "_":
                    word = ch + word
                else:
                    break
            if word in _SNIPPETS:
                start = widget.index(f"insert - {len(word)}c")
                widget.delete(start, "insert")
                widget.insert("insert", _SNIPPETS[word])
                return "break"
        except Exception:
            pass
        return None
