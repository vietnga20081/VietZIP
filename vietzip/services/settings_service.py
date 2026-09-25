"""Application settings service with JSON persistence."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any


def get_config_dir() -> Path:
    """Xác định thư mục lưu cấu hình người dùng."""
    if sys.platform == "win32":
        appdata = os.environ.get("APPDATA")
        if appdata:
            base = Path(appdata) / "VietZIP"
        else:
            base = Path.home() / ".vietzip"
    else:
        base = Path.home() / ".config" / "vietzip"

    base.mkdir(parents=True, exist_ok=True)
    return base


DEFAULT_SETTINGS: dict[str, Any] = {
    "theme": "System",                          # "System" | "Light" | "Dark"
    "compression_level": 6,                    # 0, 3, 6, 9
    "verify_archive": True,                    # Kiểm tra CRC sau khi nén
    "warn_large_archive": True,                # Cảnh báo Zip Bomb / archive lớn
    "large_archive_threshold_gb": 10.0,        # Ngưỡng cảnh báo GB
    "open_folder_after_operation": True,       # Tự mở thư mục sau khi hoàn thành
    "overwrite_policy": "auto_rename",         # "auto_rename" | "overwrite" | "skip"
    "default_output_dir": "",                  # Thư mục lưu mặc định
    "history_enabled": True,                   # Bật ghi lịch sử
    "show_mascot": True,                       # Hiển thị logo VietZIP ở màn hình trống
    "create_subfolder": True,                  # Giải nén vào thư mục con theo tên ZIP
    "filename_behavior": "smart",              # "smart" (theo tên nguồn) | "timestamp" (VietZIP_ngày_giờ)
    "last_output_dir": "",                     # Thư mục ZIP đầu ra người dùng chọn gần nhất
    "last_extract_dir": "",                    # Thư mục giải nén người dùng chọn gần nhất
}


class SettingsService:
    """Quản lý cài đặt ứng dụng VietZIP."""

    def __init__(self, config_path: Path | None = None):
        if config_path is None:
            self.config_file = get_config_dir() / "settings.json"
        else:
            self.config_file = Path(config_path)
        self.settings: dict[str, Any] = dict(DEFAULT_SETTINGS)
        self.load()

    def load(self) -> None:
        """Đọc cài đặt từ file JSON."""
        if not self.config_file.exists():
            self.save()
            return

        try:
            with open(self.config_file, "r", encoding="utf-8") as fp:
                data = json.load(fp)
                if isinstance(data, dict):
                    self.settings.update(data)
        except Exception:
            # Fallback về default nếu file bị hỏng
            self.settings = dict(DEFAULT_SETTINGS)

    def save(self) -> None:
        """Ghi cài đặt ra file JSON."""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, "w", encoding="utf-8") as fp:
                json.dump(self.settings, fp, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def get(self, key: str, default: Any = None) -> Any:
        return self.settings.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self.settings[key] = value
        self.save()


settings_service = SettingsService()
