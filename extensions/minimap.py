"""
Minimap — Extension for SCC Editor

Shows a zoomed-out minimap of the code on the right side of the editor
for quick navigation.  Click on the minimap to jump to that position.

Uses PIL/Pillow for efficient single-image rendering instead of thousands
of canvas objects.  Falls back to canvas rectangles if Pillow is unavailable.
"""
import hashlib
import tkinter as tk
from extension_api import BaseExtension

try:
    from PIL import Image, ImageDraw, ImageTk
    _HAS_PIL = True
except ImportError:
    _HAS_PIL = False


# Colour palette (RGB tuples for PIL)
_CODE_FG    = (88, 91, 112)
_KW_FG      = (137, 180, 250)
_STR_FG     = (243, 139, 168)
_COMMENT_FG = (69, 71, 90)
_BG         = (24, 24, 37)
_VP_OUTLINE = (137, 180, 250)

_KEYWORDS = frozenset({
    "if", "else", "for", "while", "return", "break", "continue",
    "class", "struct", "int", "void", "auto", "include", "using",
    "namespace", "public", "private", "template", "switch", "case",
})


class MinimapExtension(BaseExtension):
    name = "Minimap"
    version = "1.1.0"
    description = "Zoomed-out code minimap sidebar for quick navigation."
    author = "SCC Team"
    icon = "🗺️"
    category = "Appearance"
    tags = ["minimap", "navigation", "overview"]

    def __init__(self):
        super().__init__()
        self._frame = None
        self._canvas = None
        self._last_hash = ""
        self._tk_image = None      # prevent GC of PhotoImage
        self._bindings = []        # event bindings for cleanup
        self._debounce_id = None

    def activate(self, editor):
        parent = editor.text.master  # top_frame
        self._frame = tk.Frame(parent, bg="#181825", width=100)
        self._frame.pack(side="right", fill="y")
        self._frame.pack_propagate(False)

        self._canvas = tk.Canvas(
            self._frame, bg="#181825", highlightthickness=0, width=90
        )
        self._canvas.pack(fill="both", expand=True, padx=2, pady=2)
        self._canvas.bind("<Button-1>", lambda e: self._on_click(editor, e))

        # Event-driven updates instead of polling
        events = ("<KeyRelease>", "<Button-1>", "<ButtonRelease-1>")
        for ev in events:
            bid = editor.text.bind(ev, lambda e: self._debounced_draw(editor), add=True)
            self._bindings.append((ev, bid))

        # Also redraw on scroll
        scroll_bid = editor.text.bind("<MouseWheel>", lambda e: self._debounced_draw(editor), add=True)
        self._bindings.append(("<MouseWheel>", scroll_bid))
        for btn in ("<Button-4>", "<Button-5>"):
            bid = editor.text.bind(btn, lambda e: self._debounced_draw(editor), add=True)
            self._bindings.append((btn, bid))

        # Initial draw
        self._do_draw(editor)
        self.show_notification(editor, "Minimap enabled")

    def deactivate(self, editor):
        if self._debounce_id:
            try:
                editor.root.after_cancel(self._debounce_id)
            except Exception:
                pass
            self._debounce_id = None
        for ev, bid in self._bindings:
            try:
                editor.text.unbind(ev, bid)
            except Exception:
                pass
        self._bindings.clear()
        if self._frame:
            self._frame.destroy()
            self._frame = None
        self._canvas = None
        self._tk_image = None
        self._last_hash = ""

    def _debounced_draw(self, editor):
        """Debounce rapid events (200ms) to avoid excessive redraws."""
        if self._debounce_id:
            try:
                editor.root.after_cancel(self._debounce_id)
            except Exception:
                pass
        self._debounce_id = editor.root.after(200, lambda: self._do_draw(editor))

    def _do_draw(self, editor):
        """Check if content changed, then draw."""
        self._debounce_id = None
        if not self._canvas:
            return
        text = self.get_text(editor)
        content_hash = hashlib.md5(text.encode("utf-8", errors="ignore")).hexdigest()
        if content_hash != self._last_hash:
            self._last_hash = content_hash
            if _HAS_PIL:
                self._draw_pil(editor, text)
            else:
                self._draw_canvas(editor, text)
        else:
            # Content unchanged — just update the viewport indicator
            if _HAS_PIL:
                self._draw_pil(editor, text)  # PIL redraws are cheap (single image)
            else:
                self._update_viewport_canvas(editor, text)

    # ── PIL-based rendering (single image, very efficient) ───────────
    def _draw_pil(self, editor, text):
        c = self._canvas
        if not c:
            return

        cw = c.winfo_width() or 90
        ch = c.winfo_height() or 400

        lines = text.split("\n")
        total = len(lines)
        line_h = max(1, min(3, ch / max(total, 1)))

        img = Image.new("RGB", (cw, ch), _BG)
        draw = ImageDraw.Draw(img)

        for i, line in enumerate(lines):
            y = int(i * line_h)
            if y >= ch:
                break
            stripped = line.rstrip()
            if not stripped:
                continue

            s = stripped.lstrip()
            if s.startswith("//") or s.startswith("/*"):
                fg = _COMMENT_FG
            elif '"' in s or "'" in s:
                fg = _STR_FG
            elif any(w in s.split() for w in _KEYWORDS):
                fg = _KW_FG
            else:
                fg = _CODE_FG

            indent = len(line) - len(line.lstrip())
            x1 = int(min(indent * 1.5, cw * 0.4))
            x2 = int(min(x1 + len(stripped) * 0.8, cw - 2))
            h = max(1, int(line_h))

            draw.rectangle([x1, y, x2, y + h], fill=fg)

        # Viewport indicator
        try:
            first_vis = editor.text.index("@0,0")
            last_vis = editor.text.index(f"@0,{editor.text.winfo_height()}")
            fl = int(first_vis.split(".")[0])
            ll = int(last_vis.split(".")[0])
            vy1 = int((fl - 1) * line_h)
            vy2 = int(ll * line_h)
            # Semi-transparent viewport overlay
            overlay = Image.new("RGBA", (cw, vy2 - vy1), (137, 180, 250, 40))
            img.paste(
                Image.alpha_composite(
                    img.crop((0, vy1, cw, vy2)).convert("RGBA"), overlay
                ).convert("RGB"),
                (0, vy1),
            )
            draw = ImageDraw.Draw(img)
            draw.rectangle([0, vy1, cw - 1, vy2], outline=_VP_OUTLINE, width=1)
        except Exception:
            pass

        # Place on canvas as a single PhotoImage
        self._tk_image = ImageTk.PhotoImage(img)
        c.delete("all")
        c.create_image(0, 0, anchor="nw", image=self._tk_image)

    # ── Canvas fallback (no Pillow) ──────────────────────────────────
    def _draw_canvas(self, editor, text):
        c = self._canvas
        if not c:
            return
        c.delete("all")

        lines = text.split("\n")
        total = len(lines)

        cw = c.winfo_width() or 90
        ch = c.winfo_height() or 400
        line_h = max(1, min(3, ch / max(total, 1)))

        for i, line in enumerate(lines):
            y = i * line_h
            if y > ch:
                break
            stripped = line.rstrip()
            if not stripped:
                continue
            s = stripped.lstrip()
            if s.startswith("//") or s.startswith("/*"):
                fg = "#45475a"
            elif '"' in s or "'" in s:
                fg = "#f38ba8"
            elif any(w in s.split() for w in _KEYWORDS):
                fg = "#89b4fa"
            else:
                fg = "#585b70"

            indent = len(line) - len(line.lstrip())
            x1 = min(indent * 1.5, cw * 0.4)
            x2 = min(x1 + len(stripped) * 0.8, cw - 2)
            c.create_rectangle(x1, y, x2, y + line_h, fill=fg, outline="")

        self._draw_viewport_rect(editor, lines, line_h, cw)

    def _update_viewport_canvas(self, editor, text):
        if not self._canvas:
            return
        self._canvas.delete("viewport")
        lines = text.split("\n")
        total = len(lines)
        ch = self._canvas.winfo_height() or 400
        line_h = max(1, min(3, ch / max(total, 1)))
        cw = self._canvas.winfo_width() or 90
        self._draw_viewport_rect(editor, lines, line_h, cw)

    def _draw_viewport_rect(self, editor, lines, line_h, cw):
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
