"""Formatting utilities for display."""

from __future__ import annotations

from datetime import datetime
from typing import Optional


def human_size(num_bytes: float | int) -> str:
    """Đổi số byte thành chuỗi dễ đọc: 1.2 MB, 340 KB, ..."""
    num = float(num_bytes)
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if abs(num) < 1024.0:
            if unit == "B":
                return f"{int(num)} {unit}"
            return f"{num:3.1f} {unit}"
        num /= 1024.0
    return f"{num:.1f} PB"


def format_speed(bytes_per_sec: float) -> str:
    """Định dạng tốc độ truyền dữ liệu: 86.4 MB/s, 1.2 KB/s."""
    if bytes_per_sec <= 0:
        return "0 B/s"
    return f"{human_size(bytes_per_sec)}/s"


def format_eta(seconds: Optional[float]) -> str:
    """Định dạng thời gian còn lại (ETA): 00:08, 01:42, 12:35."""
    if seconds is None or seconds < 0:
        return "--:--"
    if seconds > 86400:  # > 24 hours
        return "> 24h"

    sec = int(seconds)
    hours = sec // 3600
    minutes = (sec % 3600) // 60
    secs = sec % 60

    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def format_percent(fraction: float) -> str:
    """Định dạng phần trăm: 72.5%."""
    val = max(0.0, min(1.0, fraction)) * 100
    return f"{val:.1f}%"


def format_timestamp(dt: Optional[datetime] = None) -> str:
    """Định dạng ngày giờ chuẩn hiển thị."""
    if dt is None:
        dt = datetime.now()
    return dt.strftime("%Y-%m-%d %H:%M:%S")
