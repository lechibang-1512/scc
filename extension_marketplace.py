"""
extension_marketplace.py

Open VSX-inspired Tkinter UI to browse, install, enable/disable, and
uninstall extensions.  Opens as a Toplevel window from the main editor.
"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from extension_manager import ExtensionManager


# ── Colour palette (Catppuccin Mocha-inspired) ───────────────────────
BG            = "#1e1e2e"
BG_CARD       = "#2a2a3d"
BG_CARD_HOVER = "#33334d"
BG_SIDEBAR    = "#16161e"
FG            = "#cdd6f4"
FG_DIM        = "#7f849c"
ACCENT        = "#89b4fa"
ACCENT_HOVER  = "#74c7ec"
GREEN         = "#a6e3a1"
RED           = "#f38ba8"
YELLOW        = "#f9e2af"
ORANGE        = "#fab387"
BORDER        = "#45475a"
SEARCH_BG     = "#313244"
BTN_BG        = "#45475a"
DETAIL_BG     = "#232336"


def _deep_configure(widget, **kwargs):
    """Recursively configure bg/fg on a widget tree."""
    try:
        widget.configure(**kwargs)
    except Exception:
        pass
    for child in widget.winfo_children():
        _deep_configure(child, **kwargs)


class ExtensionMarketplace(tk.Toplevel):
    """Marketplace dialog — lists installed & available extensions."""

    def __init__(self, master: tk.Tk, manager: "ExtensionManager"):
        super().__init__(master)
        self.manager = manager
        self.title("🧩  Extensions Marketplace")
        self.geometry("850x620")
        self.minsize(700, 480)
        self.configure(bg=BG)
        self.resizable(True, True)

        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", lambda *_: self._refresh())
        self._current_tab = "installed"

        # category filter
        from extension_manager import CATEGORIES
        self._categories = CATEGORIES
        self._cat_var = tk.StringVar(value="All")
        self._cat_var.trace_add("write", lambda *_: self._refresh())

        self._detail_frame: tk.Frame | None = None

        self._build_ui()
        self._refresh()

    # ── UI construction ──────────────────────────────────────────────
    def _build_ui(self):
        # Header
        header = tk.Frame(self, bg=BG)
        header.pack(fill="x", padx=16, pady=(14, 4))
        tk.Label(header, text="Extensions Marketplace", bg=BG, fg=FG,
                 font=("Segoe UI", 16, "bold")).pack(side="left")

        # Search bar
        search_outer = tk.Frame(self, bg=BG)
        search_outer.pack(fill="x", padx=16, pady=(4, 6))

        search_frame = tk.Frame(search_outer, bg=SEARCH_BG,
                                highlightbackground=BORDER, highlightthickness=1)
        search_frame.pack(side="left", fill="x", expand=True)
        tk.Label(search_frame, text="🔍", bg=SEARCH_BG, fg=FG_DIM,
                 font=("Segoe UI Emoji", 12)).pack(side="left", padx=(8, 2))
        self._search_entry = tk.Entry(
            search_frame, textvariable=self._search_var,
            bg=SEARCH_BG, fg=FG, insertbackground=FG,
            font=("Consolas", 11), bd=0, highlightthickness=0,
        )
        self._search_entry.pack(side="left", fill="x", expand=True, padx=4, pady=6)

        # Category filter
        cat_frame = tk.Frame(search_outer, bg=BG)
        cat_frame.pack(side="left", padx=(8, 0))
        tk.Label(cat_frame, text="Category:", bg=BG, fg=FG_DIM,
                 font=("Segoe UI", 10)).pack(side="left", padx=(0, 4))
        cat_combo = ttk.Combobox(cat_frame, values=self._categories, width=12,
                                 textvariable=self._cat_var, state="readonly")
        cat_combo.pack(side="left")

        # Tab bar with counts
        tab_bar = tk.Frame(self, bg=BG)
        tab_bar.pack(fill="x", padx=16, pady=(2, 6))
        self._tab_btns: dict[str, tk.Label] = {}
        for tab_id, label in (("installed", "📦 Installed"), ("available", "🌐 Available")):
            btn = tk.Label(
                tab_bar, text=label, bg=BG, fg=FG, cursor="hand2",
                font=("Segoe UI", 11, "bold"), padx=16, pady=6,
            )
            btn.pack(side="left")
            btn.bind("<Button-1>", lambda e, t=tab_id: self._switch_tab(t))
            btn.bind("<Enter>", lambda e, b=btn: b.configure(fg=ACCENT_HOVER))
            btn.bind("<Leave>", lambda e, b=btn, t=tab_id: b.configure(
                fg=ACCENT if t == self._current_tab else FG))
            self._tab_btns[tab_id] = btn

        # separator
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", padx=16)

        # Main content area: list + optional detail panel
        self._main = tk.Frame(self, bg=BG)
        self._main.pack(fill="both", expand=True, padx=16, pady=8)

        # scrollable card list (left side)
        self._list_container = tk.Frame(self._main, bg=BG)
        self._list_container.pack(side="left", fill="both", expand=True)

        self._canvas = tk.Canvas(self._list_container, bg=BG, highlightthickness=0)
        self._scrollbar = ttk.Scrollbar(self._list_container, orient="vertical",
                                        command=self._canvas.yview)
        self._inner = tk.Frame(self._canvas, bg=BG)

        self._inner.bind("<Configure>",
                         lambda e: self._canvas.configure(scrollregion=self._canvas.bbox("all")))
        self._canvas_win = self._canvas.create_window((0, 0), window=self._inner, anchor="nw")
        self._canvas.configure(yscrollcommand=self._scrollbar.set)

        self._canvas.pack(side="left", fill="both", expand=True)
        self._scrollbar.pack(side="right", fill="y")

        self._canvas.bind("<Configure>", self._on_canvas_resize)
        # mouse wheel scroll (Linux)
        self.bind_all("<Button-4>", lambda e: self._canvas.yview_scroll(-3, "units"))
        self.bind_all("<Button-5>", lambda e: self._canvas.yview_scroll(3, "units"))
        self.bind_all("<MouseWheel>", self._on_mousewheel)

        # Bottom status
        self._status = tk.Label(self, text="", bg=BG, fg=FG_DIM,
                                font=("Segoe UI", 9), anchor="w")
        self._status.pack(fill="x", padx=16, pady=(0, 8))

    def _on_canvas_resize(self, event):
        self._canvas.itemconfig(self._canvas_win, width=event.width)

    def _on_mousewheel(self, event):
        self._canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    # ── Tab switching ────────────────────────────────────────────────
    def _switch_tab(self, tab_id: str):
        self._current_tab = tab_id
        for tid, btn in self._tab_btns.items():
            btn.configure(fg=ACCENT if tid == tab_id else FG)
        self._close_detail()
        self._refresh()

    # ── Refresh list ─────────────────────────────────────────────────
    def _refresh(self):
        for w in self._inner.winfo_children():
            w.destroy()

        query = self._search_var.get().lower().strip()
        cat = self._cat_var.get()

        if self._current_tab == "installed":
            items = self._get_installed(query, cat)
        else:
            items = self._get_available(query, cat)

        if not items:
            empty = tk.Label(self._inner,
                             text="No extensions found." if query or cat != "All"
                                  else "No extensions yet.",
                             bg=BG, fg=FG_DIM, font=("Segoe UI", 12), pady=40)
            empty.pack()

        count = len(items)
        # update tab label counts
        installed_count = len(self.manager.extensions)
        available_count = len(self.manager.list_marketplace())
        self._tab_btns["installed"].config(text=f"📦 Installed ({installed_count})")
        self._tab_btns["available"].config(text=f"🌐 Available ({available_count})")
        self._status.config(
            text=f"Showing {count} extension{'s' if count != 1 else ''}"
        )

    # ── Card builders ────────────────────────────────────────────────
    def _matches_cat(self, item_cat: str, selected: str) -> bool:
        return selected == "All" or item_cat == selected

    def _get_installed(self, query: str, cat: str):
        items = []
        for name, info in sorted(self.manager.extensions.items()):
            if query and query not in info.name.lower() and query not in name.lower():
                continue
            if not self._matches_cat(info.category, cat):
                continue
            items.append(info)
            self._make_installed_card(info)
        return items

    def _get_available(self, query: str, cat: str):
        marketplace_items = self.manager.list_marketplace()
        items = []
        for meta in marketplace_items:
            if query and query not in meta.get("name", "").lower() \
                    and query not in meta.get("module_name", "").lower():
                continue
            if not self._matches_cat(meta.get("category", "Other"), cat):
                continue
            items.append(meta)
            self._make_available_card(meta)
        return items

    # ── Installed card ───────────────────────────────────────────────
    def _make_installed_card(self, info):
        card = tk.Frame(self._inner, bg=BG_CARD,
                        highlightbackground=BORDER, highlightthickness=1)
        card.pack(fill="x", pady=4, ipady=6)
        card.bind("<Enter>", lambda e, c=card: _deep_configure(c, bg=BG_CARD_HOVER))
        card.bind("<Leave>", lambda e, c=card: _deep_configure(c, bg=BG_CARD))

        left = tk.Frame(card, bg=BG_CARD)
        left.pack(side="left", fill="both", expand=True, padx=12, pady=4)

        header = tk.Frame(left, bg=BG_CARD)
        header.pack(fill="x")
        tk.Label(header, text=info.icon, bg=BG_CARD, fg=FG,
                 font=("Segoe UI Emoji", 16)).pack(side="left", padx=(0, 8))
        tk.Label(header, text=info.name, bg=BG_CARD, fg=FG,
                 font=("Segoe UI", 12, "bold")).pack(side="left")
        tk.Label(header, text=f"v{info.version}", bg=BG_CARD, fg=FG_DIM,
                 font=("Segoe UI", 9)).pack(side="left", padx=(8, 0))

        # status / error badge
        if info.error:
            tk.Label(header, text="⚠ Error", bg=BG_CARD, fg=RED,
                     font=("Segoe UI", 9, "bold")).pack(side="left", padx=(12, 0))
        else:
            clr = GREEN if info.enabled else YELLOW
            txt = "● Enabled" if info.enabled else "● Disabled"
            tk.Label(header, text=txt, bg=BG_CARD, fg=clr,
                     font=("Segoe UI", 9)).pack(side="left", padx=(12, 0))

        # category pill
        tk.Label(header, text=info.category, bg=BORDER, fg=FG_DIM,
                 font=("Segoe UI", 8), padx=6, pady=1).pack(side="left", padx=(8, 0))

        tk.Label(left, text=info.description, bg=BG_CARD, fg=FG_DIM,
                 font=("Segoe UI", 10), anchor="w",
                 wraplength=380).pack(fill="x", pady=(2, 0))
        tk.Label(left, text=f"by {info.author}", bg=BG_CARD, fg=FG_DIM,
                 font=("Segoe UI", 9, "italic"), anchor="w").pack(fill="x")

        # right: buttons
        right = tk.Frame(card, bg=BG_CARD)
        right.pack(side="right", padx=12, pady=4)

        # detail button
        self._action_btn(right, "Details", ACCENT,
                         lambda i=info: self._show_installed_detail(i))

        if info.enabled:
            self._action_btn(right, "Disable", YELLOW,
                             lambda n=info.module_name: self._do_disable(n))
        else:
            self._action_btn(right, "Enable", GREEN,
                             lambda n=info.module_name: self._do_enable(n))

        self._action_btn(right, "Reload", ORANGE,
                         lambda n=info.module_name: self._do_reload(n))
        self._action_btn(right, "Uninstall", RED,
                         lambda n=info.module_name: self._do_uninstall(n))

    # ── Available card ───────────────────────────────────────────────
    def _make_available_card(self, meta: dict):
        card = tk.Frame(self._inner, bg=BG_CARD,
                        highlightbackground=BORDER, highlightthickness=1)
        card.pack(fill="x", pady=4, ipady=6)
        card.bind("<Enter>", lambda e, c=card: _deep_configure(c, bg=BG_CARD_HOVER))
        card.bind("<Leave>", lambda e, c=card: _deep_configure(c, bg=BG_CARD))

        left = tk.Frame(card, bg=BG_CARD)
        left.pack(side="left", fill="both", expand=True, padx=12, pady=4)

        header = tk.Frame(left, bg=BG_CARD)
        header.pack(fill="x")
        tk.Label(header, text=meta.get("icon", "🧩"), bg=BG_CARD, fg=FG,
                 font=("Segoe UI Emoji", 16)).pack(side="left", padx=(0, 8))
        tk.Label(header, text=meta.get("name", ""), bg=BG_CARD, fg=FG,
                 font=("Segoe UI", 12, "bold")).pack(side="left")
        tk.Label(header, text=f"v{meta.get('version', '?')}", bg=BG_CARD, fg=FG_DIM,
                 font=("Segoe UI", 9)).pack(side="left", padx=(8, 0))

        # category pill
        tk.Label(header, text=meta.get("category", "Other"), bg=BORDER, fg=FG_DIM,
                 font=("Segoe UI", 8), padx=6, pady=1).pack(side="left", padx=(8, 0))

        tk.Label(left, text=meta.get("description", ""), bg=BG_CARD, fg=FG_DIM,
                 font=("Segoe UI", 10), anchor="w",
                 wraplength=380).pack(fill="x", pady=(2, 0))
        tk.Label(left, text=f"by {meta.get('author', 'Unknown')}", bg=BG_CARD, fg=FG_DIM,
                 font=("Segoe UI", 9, "italic"), anchor="w").pack(fill="x")

        right = tk.Frame(card, bg=BG_CARD)
        right.pack(side="right", padx=12, pady=4)
        self._action_btn(right, "Install", GREEN,
                         lambda fp=meta["file_path"]: self._do_install(fp))

    # ── Detail panel ─────────────────────────────────────────────────
    def _show_installed_detail(self, info):
        self._close_detail()

        self._detail_frame = tk.Frame(self._main, bg=DETAIL_BG, width=280,
                                      highlightbackground=BORDER, highlightthickness=1)
        self._detail_frame.pack(side="right", fill="y", padx=(8, 0))
        self._detail_frame.pack_propagate(False)

        inner = tk.Frame(self._detail_frame, bg=DETAIL_BG)
        inner.pack(fill="both", expand=True, padx=12, pady=12)

        # close btn
        close = tk.Label(inner, text="✕", bg=DETAIL_BG, fg=FG_DIM, cursor="hand2",
                         font=("Segoe UI", 14))
        close.pack(anchor="ne")
        close.bind("<Button-1>", lambda e: self._close_detail())

        tk.Label(inner, text=info.icon, bg=DETAIL_BG, fg=FG,
                 font=("Segoe UI Emoji", 32)).pack(pady=(4, 8))
        tk.Label(inner, text=info.name, bg=DETAIL_BG, fg=FG,
                 font=("Segoe UI", 14, "bold")).pack()
        tk.Label(inner, text=f"v{info.version}  •  {info.category}", bg=DETAIL_BG,
                 fg=FG_DIM, font=("Segoe UI", 10)).pack(pady=(2, 4))
        tk.Label(inner, text=f"by {info.author}", bg=DETAIL_BG, fg=FG_DIM,
                 font=("Segoe UI", 10, "italic")).pack()

        sep = tk.Frame(inner, bg=BORDER, height=1)
        sep.pack(fill="x", pady=10)

        desc = tk.Label(inner, text=info.description or "(no description)", bg=DETAIL_BG,
                        fg=FG, font=("Segoe UI", 10), wraplength=240, justify="left",
                        anchor="nw")
        desc.pack(fill="x")

        # settings info
        if info.has_settings and info.instance:
            sep2 = tk.Frame(inner, bg=BORDER, height=1)
            sep2.pack(fill="x", pady=10)
            tk.Label(inner, text="⚙  Settings", bg=DETAIL_BG, fg=ACCENT,
                     font=("Segoe UI", 11, "bold"), anchor="w").pack(fill="x")
            defaults = info.instance.default_settings()
            for k, v in defaults.items():
                cur = info.instance.get_setting(k)
                tk.Label(inner, text=f"{k}: {cur}", bg=DETAIL_BG, fg=FG_DIM,
                         font=("Consolas", 9), anchor="w").pack(fill="x", padx=(8, 0))

        # error info
        if info.error:
            sep3 = tk.Frame(inner, bg=BORDER, height=1)
            sep3.pack(fill="x", pady=10)
            tk.Label(inner, text="⚠  Error Details", bg=DETAIL_BG, fg=RED,
                     font=("Segoe UI", 11, "bold"), anchor="w").pack(fill="x")
            err_text = tk.Text(inner, bg="#1a1a2a", fg=RED, font=("Consolas", 8),
                               height=6, wrap="word", bd=0)
            err_text.pack(fill="x", pady=(4, 0))
            err_text.insert("1.0", info.error)
            err_text.config(state="disabled")

    def _close_detail(self):
        if self._detail_frame:
            self._detail_frame.destroy()
            self._detail_frame = None

    # ── Action button ────────────────────────────────────────────────
    def _action_btn(self, parent, text, fg_color, command):
        btn = tk.Label(
            parent, text=text, bg=BTN_BG, fg=fg_color,
            font=("Segoe UI", 10, "bold"), padx=14, pady=4,
            cursor="hand2", relief="flat",
        )
        btn.pack(side="top", pady=2)
        btn.bind("<Button-1>", lambda e: command())
        btn.bind("<Enter>", lambda e, b=btn: b.configure(bg=BORDER))
        btn.bind("<Leave>", lambda e, b=btn: b.configure(bg=BTN_BG))

    # ── Actions ──────────────────────────────────────────────────────
    def _do_enable(self, mod_name: str):
        self.manager.enable(mod_name)
        self._refresh()

    def _do_disable(self, mod_name: str):
        self.manager.disable(mod_name)
        self._refresh()

    def _do_reload(self, mod_name: str):
        self.manager.reload_extension(mod_name)
        self._refresh()

    def _do_uninstall(self, mod_name: str):
        if messagebox.askyesno("Uninstall", f"Remove '{mod_name}'?", parent=self):
            self.manager.uninstall(mod_name)
            self._close_detail()
            self._refresh()

    def _do_install(self, file_path: str):
        ok = self.manager.install_from_marketplace(Path(file_path))
        if ok:
            self._switch_tab("installed")
        else:
            messagebox.showwarning("Install",
                                   "Extension is already installed or failed.",
                                   parent=self)

    def destroy(self):
        try:
            self.unbind_all("<MouseWheel>")
            self.unbind_all("<Button-4>")
            self.unbind_all("<Button-5>")
        except Exception:
            pass
        super().destroy()
