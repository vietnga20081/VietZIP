"""Recent files tracking service."""

from __future__ import annotations

import json
from pathlib import Path
from typing import List

from vietzip.services.settings_service import get_config_dir


class RecentService:
    """Quản lý danh sách các file ZIP đã mở gần đây."""

    def __init__(self, recent_file: Path | None = None, max_items: int = 10):
        if recent_file is None:
            self.recent_file = get_config_dir() / "recent.json"
        else:
            self.recent_file = Path(recent_file)
        self.max_items = max_items
        self.items: list[str] = []
        self.load()

    def load(self) -> None:
        """Đọc danh sách file gần đây."""
        if not self.recent_file.exists():
            return
        try:
            with open(self.recent_file, "r", encoding="utf-8") as fp:
                data = json.load(fp)
                if isinstance(data, list):
                    # Chỉ giữ lại các file còn tồn tại
                    self.items = [item for item in data if Path(item).exists()][: self.max_items]
        except Exception:
            self.items = []

    def save(self) -> None:
        """Ghi danh sách file gần đây ra JSON."""
        try:
            self.recent_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.recent_file, "w", encoding="utf-8") as fp:
                json.dump(self.items, fp, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def add(self, file_path: str | Path) -> None:
        """Thêm một file vào danh sách gần đây (đẩy lên đầu, loại trùng)."""
        resolved = str(Path(file_path).resolve())
        if resolved in self.items:
            self.items.remove(resolved)
        self.items.insert(0, resolved)
        if len(self.items) > self.max_items:
            self.items = self.items[: self.max_items]
        self.save()

    def get_all(self) -> list[str]:
        """Lấy danh sách các file còn tồn tại."""
        valid = [item for item in self.items if Path(item).exists()]
        if len(valid) != len(self.items):
            self.items = valid
            self.save()
        return list(self.items)

    def clear(self) -> None:
        """Xóa toàn bộ danh sách gần đây."""
        self.items = []
        self.save()


recent_service = RecentService()
