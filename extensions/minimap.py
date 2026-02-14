"""
Minimap — Extension for SCC Editor

Shows a zoomed-out minimap of the code on the right side of the editor
for quick navigation.  Click on the minimap to jump to that position.
"""
import hashlib
import tkinter as tk
from extension_api import BaseExtension


class MinimapExtension(BaseExtension):
    name = "Minimap"
    version = "1.0.0"
    description = "Zoomed-out code minimap sidebar for quick navigation."
    author = "SCC Team"
    icon = "🗺️"
    category = "Appearance"
    tags = ["minimap", "navigation", "overview"]

    def __init__(self):
        super().__init__()
        self._frame = None
        self._canvas = None
        self._after_id = None
        self._last_hash = ""  # content hash for dirty checking

    def activate(self, editor):
        # Create minimap frame to the right of the text widget
        parent = editor.text.master  # top_frame
        self._frame = tk.Frame(parent, bg="#181825", width=100)
        self._frame.pack(side="right", fill="y")
        self._frame.pack_propagate(False)

        self._canvas = tk.Canvas(
            self._frame, bg="#181825", highlightthickness=0, width=90
        )
        self._canvas.pack(fill="both", expand=True, padx=2, pady=2)
        self._canvas.bind("<Button-1>", lambda e: self._on_click(editor, e))

        self._schedule(editor)
        self.show_notification(editor, "Minimap enabled")

    def deactivate(self, editor):
        if self._after_id:
            try:
                editor.root.after_cancel(self._after_id)
            except Exception:
                pass
            self._after_id = None
        if self._frame:
            self._frame.destroy()
            self._frame = None
        self._canvas = None
        self._last_hash = ""

    def _schedule(self, editor):
        self._maybe_draw(editor)
        self._after_id = editor.root.after(1000, lambda: self._schedule(editor))

    def _maybe_draw(self, editor):
        """Only redraw if text content has changed (dirty-flag via hash)."""
        text = self.get_text(editor)
        # Use a fast hash to detect content changes
        content_hash = hashlib.md5(text.encode("utf-8", errors="ignore")).hexdigest()
        if content_hash != self._last_hash:
            self._last_hash = content_hash
            self._draw(editor, text)
        else:
            # Still update the viewport indicator (cursor may have moved)
            self._update_viewport(editor, text)

    def _draw(self, editor, text=None):
        if not self._canvas:
            return
        c = self._canvas

        if text is None:
            text = self.get_text(editor)
        lines = text.split("\n")
        if not lines:
            c.delete("all")
            return

        c.delete("all")

        cw = c.winfo_width() or 90
        ch = c.winfo_height() or 400

        total = len(lines)
        line_h = max(1, min(3, ch / max(total, 1)))

        # colours
        code_fg = "#585b70"
        kw_fg = "#89b4fa"
        str_fg = "#f38ba8"
        comment_fg = "#45475a"

        keywords = {
            "if", "else", "for", "while", "return", "break", "continue",
            "class", "struct", "int", "void", "auto", "include", "using",
            "namespace", "public", "private", "template", "switch", "case",
        }

        for i, line in enumerate(lines):
            y = i * line_h
            if y > ch:
                break
            stripped = line.rstrip()
            if not stripped:
                continue

            # determine colour
            s = stripped.lstrip()
            if s.startswith("//") or s.startswith("/*"):
                fg = comment_fg
            elif '"' in s or "'" in s:
                fg = str_fg
            elif any(w in s.split() for w in keywords):
                fg = kw_fg
            else:
                fg = code_fg

            indent = len(line) - len(line.lstrip())
            x1 = min(indent * 1.5, cw * 0.4)
            x2 = min(x1 + len(stripped) * 0.8, cw - 2)

            c.create_rectangle(x1, y, x2, y + line_h, fill=fg, outline="")

        # viewport indicator
        self._draw_viewport(editor, lines, line_h, cw)

    def _update_viewport(self, editor, text=None):
        """Update only the viewport indicator without redrawing all content."""
        if not self._canvas:
            return
        c = self._canvas
        # Remove old viewport indicator
        c.delete("viewport")
        if text is None:
            text = self.get_text(editor)
        lines = text.split("\n")
        total = len(lines)
        ch = c.winfo_height() or 400
        line_h = max(1, min(3, ch / max(total, 1)))
        cw = c.winfo_width() or 90
        self._draw_viewport(editor, lines, line_h, cw)

    def _draw_viewport(self, editor, lines, line_h, cw):
        """Draw the viewport indicator rectangle."""
        try:
            first_vis = editor.text.index("@0,0")
            last_vis = editor.text.index(f"@0,{editor.text.winfo_height()}")
            fl = int(first_vis.split(".")[0])
            ll = int(last_vis.split(".")[0])
            vy1 = (fl - 1) * line_h
            vy2 = ll * line_h
            self._canvas.create_rectangle(
                0, vy1, cw, vy2,
                fill="", outline="#89b4fa", width=1, stipple="gray25",
                tags="viewport"
            )
        except Exception:
            pass

    def _on_click(self, editor, event):
        """Jump to the clicked position in the minimap."""
        if not self._canvas:
            return
        text = self.get_text(editor)
        lines = text.split("\n")
        total = len(lines)
        ch = self._canvas.winfo_height() or 400
        line_h = max(1, min(3, ch / max(total, 1)))
        target_line = int(event.y / line_h) + 1
        target_line = max(1, min(target_line, total))
        editor.text.see(f"{target_line}.0")
        editor.text.mark_set("insert", f"{target_line}.0")
