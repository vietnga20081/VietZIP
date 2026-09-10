"""Operation history service with JSON persistence."""

from __future__ import annotations

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from vietzip.services.settings_service import get_config_dir


class HistoryService:
    """Quản lý lịch sử nén và giải nén."""

    def __init__(self, history_file: Path | None = None, max_records: int = 300):
        if history_file is None:
            self.history_file = get_config_dir() / "history.json"
        else:
            self.history_file = Path(history_file)
        self.max_records = max_records
        self.records: list[dict[str, Any]] = []
        self.load()

    def load(self) -> None:
        """Đọc danh sách lịch sử từ file JSON."""
        if not self.history_file.exists():
            return
        try:
            with open(self.history_file, "r", encoding="utf-8") as fp:
                data = json.load(fp)
                if isinstance(data, list):
                    self.records = data[: self.max_records]
        except Exception:
            self.records = []

    def save(self) -> None:
        """Ghi danh sách lịch sử ra file JSON."""
        try:
            self.history_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.history_file, "w", encoding="utf-8") as fp:
                json.dump(self.records, fp, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def add_record(
        self,
        operation: str,
        input_summary: str,
        output_path: str,
        file_count: int,
        original_size: int,
        final_size: int,
        elapsed_seconds: float,
        status: str = "success",
        error_message: Optional[str] = None,
    ) -> None:
        """Thêm một bản ghi lịch sử mới."""
        record = {
            "id": int(time.time() * 1000),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "operation": operation,
            "input_summary": input_summary,
            "output_path": output_path,
            "file_count": file_count,
            "original_size": original_size,
            "final_size": final_size,
            "elapsed_seconds": round(elapsed_seconds, 2),
            "status": status,
            "error_message": error_message,
        }
        self.records.insert(0, record)
        if len(self.records) > self.max_records:
            self.records = self.records[: self.max_records]
        self.save()

    def get_records(self) -> list[dict[str, Any]]:
        """Lấy toàn bộ danh sách lịch sử."""
        return list(self.records)

    def remove_record(self, record_id: int) -> None:
        """Xóa một bản ghi theo ID."""
        self.records = [r for r in self.records if r.get("id") != record_id]
        self.save()

    def clear(self) -> None:
        """Xóa toàn bộ lịch sử."""
        self.records = []
        self.save()


history_service = HistoryService()
