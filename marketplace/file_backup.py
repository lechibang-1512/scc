"""
File Backup — Extension for SCC Editor

Automatically creates a .bak backup copy every time you save a file.
The backup directory is configurable via extension settings.

Storage-aware: skips the backup if file content is identical to the
most recent backup (MD5 hash comparison), reducing unnecessary SSD writes.
"""
import hashlib
import os
import shutil
from pathlib import Path
from extension_api import BaseExtension


def _file_hash(path):
    """Compute MD5 hash of a file using 8 KB chunks (fast, low memory)."""
    h = hashlib.md5()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()


class FileBackupExtension(BaseExtension):
    name = "File Backup"
    version = "1.1.0"
    description = "Auto-saves a .bak copy on every save. Skips if content unchanged. Backup directory is configurable."
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
            if not src.exists():
                return

            if backup_dir:
                dest_dir = Path(os.path.expanduser(backup_dir))
                dest_dir.mkdir(parents=True, exist_ok=True)
            else:
                dest_dir = src.parent

            base = src.stem
            ext = src.suffix

            # Find existing backups sorted by mtime (newest first)
            existing = sorted(
                dest_dir.glob(f"{base}{ext}.bak*"),
                key=lambda p: p.stat().st_mtime if p.exists() else 0,
                reverse=True,
            )

            # Skip backup if latest backup has identical content (reduce SSD wear)
            if existing:
                try:
                    if _file_hash(str(src)) == _file_hash(str(existing[0])):
                        self.set_status(editor, "Backup skipped — no changes")
                        return
                except Exception:
                    pass  # hash failed, proceed with backup

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
