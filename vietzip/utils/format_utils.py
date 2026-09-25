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


def shorten_middle(text: str, max_chars: int = 60) -> str:
    """Rút gọn chuỗi dài ở giữa: C:\\Users\\...\\Documents\\file.txt (không làm vỡ layout)."""
    if max_chars < 8 or len(text) <= max_chars:
        return text
    keep = max_chars - 1
    head = keep // 2
    tail = keep - head
    return f"{text[:head]}…{text[-tail:]}"


def format_eta_human(seconds: Optional[float]) -> str:
    """ETA thân thiện: 'Còn khoảng 8 giây', 'Còn khoảng 2 phút 5 giây'."""
    if seconds is None or seconds < 0:
        return "Đang ước tính..."
    sec = int(round(seconds))
    if sec < 1:
        return "Sắp xong"
    if sec > 86400:
        return "Còn hơn 24 giờ"
    hours, rem = divmod(sec, 3600)
    minutes, secs = divmod(rem, 60)
    if hours:
        return f"Còn khoảng {hours} giờ {minutes} phút"
    if minutes:
        return f"Còn khoảng {minutes} phút {secs} giây"
    return f"Còn khoảng {secs} giây"


def format_duration(seconds: float) -> str:
    """Thời gian đã chạy: '8.4 giây', '2 phút 5 giây'."""
    if seconds < 60:
        return f"{seconds:.1f} giây"
    minutes, secs = divmod(int(round(seconds)), 60)
    return f"{minutes} phút {secs} giây"


def format_count(n: int) -> str:
    """Số có dấu phân cách nghìn kiểu Việt: 1.284."""
    return f"{n:,}".replace(",", ".")
