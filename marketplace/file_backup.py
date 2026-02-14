"""
File Backup — Extension for SCC Editor

Automatically creates a .bak backup copy every time you save a file.
The backup directory is configurable via extension settings.
"""
import os
import shutil
from pathlib import Path
from extension_api import BaseExtension


class FileBackupExtension(BaseExtension):
    name = "File Backup"
    version = "1.0.0"
    description = "Auto-saves a .bak copy on every save. Backup directory is configurable."
    author = "SCC Team"
    icon = "💾"
    category = "Tools"
    tags = ["backup", "save", "safety"]

    def __init__(self):
        super().__init__()

    def default_settings(self):
        return {
            "backup_dir": "",       # empty = same dir as file
            "max_backups": 5,       # keep last N backups per file
        }

    def activate(self, editor):
        self.show_notification(editor, "File Backup active — .bak on every save")

    def deactivate(self, editor):
        pass

    def on_file_save(self, editor, path: str):
        if not path:
            return
        try:
            backup_dir = self.get_setting("backup_dir")
            max_backups = int(self.get_setting("max_backups") or 5)

            src = Path(path)
            if backup_dir:
                dest_dir = Path(os.path.expanduser(backup_dir))
                dest_dir.mkdir(parents=True, exist_ok=True)
            else:
                dest_dir = src.parent

            base = src.stem
            ext = src.suffix

            # Rotate existing backups (sorted once, no repeated stat calls)
            existing = sorted(
                dest_dir.glob(f"{base}{ext}.bak*"),
                key=lambda p: p.stat().st_mtime if p.exists() else 0,
                reverse=True,
            )
            # Remove oldest if over limit
            while len(existing) >= max_backups:
                oldest = existing.pop()
                try:
                    oldest.unlink()
                except Exception:
                    pass

            idx = len(existing) + 1
            dest = dest_dir / f"{base}{ext}.bak{idx}"
            shutil.copy2(str(src), str(dest))

            self.set_status(editor, f"Backup saved: {dest.name}")
        except Exception as exc:
            self.set_status(editor, f"Backup failed: {exc}")
