"""
extension_manager.py

Handles discovery, loading, unloading, enabling/disabling, and hot-reloading
of .py extension files from the ``extensions/`` directory.
"""
from __future__ import annotations

import importlib
import importlib.util
import json
import logging
import os
import re
import sys
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional

log = logging.getLogger("scc.extensions")

from extension_api import BaseExtension

# ── Paths ────────────────────────────────────────────────────────────
EXTENSIONS_DIR = Path(__file__).parent / "extensions"
STATE_FILE = EXTENSIONS_DIR / "extensions.json"
MARKETPLACE_DIR = Path(__file__).parent / "marketplace"

# All known categories for filtering
CATEGORIES = ["All", "Appearance", "Editing", "Tools", "Languages", "Other"]


class ExtensionInfo:
    """Lightweight record that tracks a loaded extension module."""

    def __init__(
        self,
        module_name: str,
        file_path: Path,
        module: Any = None,
        instance: Optional[BaseExtension] = None,
        enabled: bool = True,
        error: Optional[str] = None,
    ):
        self.module_name = module_name
        self.file_path = file_path
        self.module = module
        self.instance = instance
        self.enabled = enabled
        self.error = error  # traceback string if load/activate failed

    # handy metadata proxies
    @property
    def name(self) -> str:
        return getattr(self.instance, "name", self.module_name) if self.instance else self.module_name

    @property
    def version(self) -> str:
        return getattr(self.instance, "version", "?") if self.instance else "?"

    @property
    def description(self) -> str:
        return getattr(self.instance, "description", "") if self.instance else ""

    @property
    def author(self) -> str:
        return getattr(self.instance, "author", "Unknown") if self.instance else "Unknown"

    @property
    def icon(self) -> str:
        return getattr(self.instance, "icon", "🧩") if self.instance else "🧩"

    @property
    def category(self) -> str:
        return getattr(self.instance, "category", "Other") if self.instance else "Other"

    @property
    def tags(self) -> list:
        return getattr(self.instance, "tags", []) if self.instance else []

    @property
    def has_settings(self) -> bool:
        if self.instance:
            return bool(self.instance.default_settings())
        return False


class ExtensionManager:
    """Central controller for the extension subsystem."""

    def __init__(self, editor: Any):
        self.editor = editor
        self.extensions: Dict[str, ExtensionInfo] = {}
        self._shutting_down = False
        log.info("Initialising extension subsystem…")
        self._ensure_dirs()
        self._load_state()
        self.discover_and_load()
        loaded = [n for n, i in self.extensions.items() if i.enabled]
        log.info("Extension subsystem ready — %d extension(s) active: %s",
                 len(loaded), ", ".join(loaded) or "(none)")

    # ── Directory / state helpers ────────────────────────────────────
    @staticmethod
    def _ensure_dirs():
        EXTENSIONS_DIR.mkdir(parents=True, exist_ok=True)
        MARKETPLACE_DIR.mkdir(parents=True, exist_ok=True)
        (EXTENSIONS_DIR / "settings").mkdir(parents=True, exist_ok=True)

    def _load_state(self):
        """Load persisted enabled/disabled flags."""
        self._state: Dict[str, bool] = {}
        if STATE_FILE.exists():
            try:
                with open(STATE_FILE, "r") as f:
                    self._state = json.load(f)
            except Exception:
                self._state = {}

    def _save_state(self):
        with open(STATE_FILE, "w") as f:
            json.dump(
                {name: info.enabled for name, info in self.extensions.items()},
                f,
                indent=2,
            )

    # ── Discovery & loading ──────────────────────────────────────────
    def discover_and_load(self):
        """Scan extensions/ for .py files, load & activate enabled ones."""
        for py_file in sorted(EXTENSIONS_DIR.glob("*.py")):
            mod_name = py_file.stem
            if mod_name.startswith("_"):
                continue
            if mod_name not in self.extensions:
                log.debug("Discovered extension file: %s", py_file.name)
                self._load_extension(py_file)

    def _load_extension(self, path: Path) -> Optional[ExtensionInfo]:
        mod_name = path.stem
        try:
            spec = importlib.util.spec_from_file_location(
                f"ext_{mod_name}", str(path)
            )
            if spec is None or spec.loader is None:
                return None
            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module
            spec.loader.exec_module(module)

            # find the Extension subclass
            ext_cls = self._find_extension_class(module)
            if ext_cls is None:
                return None

            instance = ext_cls()
            enabled = self._state.get(mod_name, True)
            info = ExtensionInfo(mod_name, path, module, instance, enabled)
            self.extensions[mod_name] = info

            if enabled:
                self._activate(info)
            return info
        except Exception as exc:
            tb = traceback.format_exc()
            info = ExtensionInfo(mod_name, path, error=tb)
            info.enabled = False
            self.extensions[mod_name] = info
            print(f"[ExtMgr] Failed to load {mod_name}:\n{tb}", file=sys.stderr)
            return info

    @staticmethod
    def _find_extension_class(module: Any):
        """Return the first BaseExtension subclass defined in *module*."""
        for attr_name in dir(module):
            obj = getattr(module, attr_name)
            if (
                isinstance(obj, type)
                and issubclass(obj, BaseExtension)
                and obj is not BaseExtension
            ):
                return obj
        return None

    # ── Activation / deactivation ────────────────────────────────────
    def _get_menubar(self):
        """Resolve the actual tk.Menu widget from the editor root."""
        try:
            menu_path = self.editor.root.cget("menu")
            if menu_path:
                return self.editor.root.nametowidget(menu_path)
        except Exception:
            pass
        return None

    def _activate(self, info: ExtensionInfo):
        try:
            if info.instance:
                log.info("Activating extension: %s", info.name)
                info.instance.activate(self.editor)
                menubar = self._get_menubar()
                if menubar:
                    info.instance.contribute_menu(self.editor, menubar)
                info.error = None
        except Exception:
            info.error = traceback.format_exc()
            log.error("Activate failed for %s:\n%s", info.module_name, info.error)

    def _deactivate(self, info: ExtensionInfo):
        try:
            if info.instance:
                log.info("Deactivating extension: %s", info.name)
                # auto-cleanup keybindings
                info.instance.unregister_all_keybindings(self.editor)
                info.instance.deactivate(self.editor)
        except Exception:
            log.exception("Deactivate failed for %s", info.module_name)

    def enable(self, mod_name: str):
        info = self.extensions.get(mod_name)
        if info and not info.enabled:
            info.enabled = True
            self._activate(info)
            self._save_state()

    def disable(self, mod_name: str):
        info = self.extensions.get(mod_name)
        if info and info.enabled:
            self._deactivate(info)
            info.enabled = False
            self._save_state()

    def uninstall(self, mod_name: str):
        info = self.extensions.get(mod_name)
        if info:
            if info.enabled:
                self._deactivate(info)
            # remove the .py file
            try:
                info.file_path.unlink(missing_ok=True)
            except Exception:
                pass
            # remove settings file
            try:
                settings_file = EXTENSIONS_DIR / "settings" / f"{mod_name}.json"
                settings_file.unlink(missing_ok=True)
            except Exception:
                pass
            # remove from sys.modules
            sys_key = f"ext_{mod_name}"
            sys.modules.pop(sys_key, None)
            del self.extensions[mod_name]
            self._save_state()

    def install_from_marketplace(self, marketplace_path: Path) -> bool:
        """Copy a .py file from marketplace/ into extensions/ and load it."""
        import shutil

        dest = EXTENSIONS_DIR / marketplace_path.name
        if dest.exists():
            return False  # already installed
        try:
            shutil.copy2(str(marketplace_path), str(dest))
            info = self._load_extension(dest)
            if info:
                self._save_state()
                return True
        except Exception:
            traceback.print_exc()
        return False

    # ── Hot-reload ───────────────────────────────────────────────────
    def reload_extension(self, mod_name: str):
        """Reload a single extension from disk."""
        info = self.extensions.get(mod_name)
        if not info:
            return
        was_enabled = info.enabled
        if was_enabled:
            self._deactivate(info)
        # reimport
        try:
            spec = importlib.util.spec_from_file_location(
                f"ext_{mod_name}", str(info.file_path)
            )
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                sys.modules[spec.name] = module
                spec.loader.exec_module(module)
                ext_cls = self._find_extension_class(module)
                if ext_cls:
                    info.module = module
                    info.instance = ext_cls()
                    info.error = None
        except Exception:
            info.error = traceback.format_exc()
            print(f"[ExtMgr] Reload failed for {mod_name}:\n{info.error}", file=sys.stderr)
        if was_enabled:
            info.enabled = True
            self._activate(info)

    def reload_all(self):
        """Reload every installed extension."""
        for mod_name in list(self.extensions.keys()):
            self.reload_extension(mod_name)
        # also pick up newly added files
        self.discover_and_load()

    # ── Shutdown ─────────────────────────────────────────────────────
    def shutdown_all(self):
        """Deactivate every extension, call on_shutdown, and save state.

        This is the single entry-point for graceful teardown at app exit.
        Safe to call multiple times (idempotent).
        """
        if self._shutting_down:
            return
        self._shutting_down = True
        log.info("Shutting down %d extension(s)…", len(self.extensions))
        for mod_name, info in list(self.extensions.items()):
            # 1. deactivate if still active
            if info.enabled and info.instance:
                self._deactivate(info)
            # 2. on_shutdown hook
            if info.instance:
                try:
                    info.instance.on_shutdown(self.editor)
                except Exception:
                    log.exception("on_shutdown failed for %s", mod_name)
        self._save_state()
        log.info("All extensions shut down.")

    # ── Event dispatch ───────────────────────────────────────────────
    def dispatch_key(self, event) -> Optional[str]:
        for info in self.extensions.values():
            if info.enabled and info.instance:
                try:
                    result = info.instance.on_key(self.editor, event)
                    if result == "break":
                        return "break"
                except Exception:
                    traceback.print_exc()
        return None

    def dispatch_file_open(self, path: str):
        for info in self.extensions.values():
            if info.enabled and info.instance:
                try:
                    info.instance.on_file_open(self.editor, path)
                except Exception:
                    traceback.print_exc()

    def dispatch_file_save(self, path: str):
        for info in self.extensions.values():
            if info.enabled and info.instance:
                try:
                    info.instance.on_file_save(self.editor, path)
                except Exception:
                    traceback.print_exc()

    def dispatch_build_start(self):
        for info in self.extensions.values():
            if info.enabled and info.instance:
                try:
                    info.instance.on_build_start(self.editor)
                except Exception:
                    traceback.print_exc()

    def dispatch_build_end(self, success: bool):
        for info in self.extensions.values():
            if info.enabled and info.instance:
                try:
                    info.instance.on_build_end(self.editor, success)
                except Exception:
                    traceback.print_exc()

    # ── Marketplace helpers ──────────────────────────────────────────
    def list_marketplace(self) -> List[Dict[str, str]]:
        """Return metadata about available (not yet installed) marketplace extensions."""
        results: List[Dict[str, str]] = []
        for py_file in sorted(MARKETPLACE_DIR.glob("*.py")):
            mod_name = py_file.stem
            if mod_name.startswith("_") or mod_name in self.extensions:
                continue
            meta = self._quick_parse_meta(py_file)
            meta["module_name"] = mod_name
            meta["file_path"] = str(py_file)
            results.append(meta)
        return results

    @staticmethod
    def _quick_parse_meta(path: Path) -> Dict[str, str]:
        """Parse class-level metadata from an extension file without importing."""
        meta: Dict[str, str] = {
            "name": path.stem.replace("_", " ").title(),
            "version": "?",
            "description": "",
            "author": "Unknown",
            "icon": "🧩",
            "category": "Other",
        }
        try:
            src = path.read_text(encoding="utf-8", errors="ignore")
            for key in ("name", "version", "description", "author", "icon", "category"):
                m = re.search(
                    rf'^\s+{key}\s*[=:]\s*["\'](.+?)["\']',
                    src,
                    re.MULTILINE,
                )
                if m:
                    meta[key] = m.group(1)
        except Exception:
            pass
        return meta
