"""Data models and enums for VietZIP."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class OverwritePolicy(str, Enum):
    """Chính sách xử lý khi file đã tồn tại."""
    OVERWRITE = "overwrite"        # Ghi đè file
    SKIP = "skip"                  # Bỏ qua file
    AUTO_RENAME = "auto_rename"    # Tự đổi tên thành file (1).ext


class OperationType(str, Enum):
    """Loại tác vụ."""
    COMPRESS = "compress"
    EXTRACT = "extract"


COMPRESSION_LEVELS = {
    "Siêu nhanh (không nén)": 0,
    "Nhanh": 3,
    "Cân bằng ⭐": 6,
    "Nén tối đa 🐢": 9,
}


@dataclass
class ProgressInfo:
    """Thông tin tiến trình chi tiết."""
    operation: str
    current_file: str
    current_index: int
    total_files: int
    processed_bytes: int
    total_bytes: int
    percent: float                # 0.0 -> 1.0
    speed_bps: float = 0.0        # Bytes per second
    eta_seconds: Optional[float] = None


@dataclass
class OperationResult:
    """Kết quả sau khi hoàn thành tác vụ."""
    success: bool
    operation: str
    output_path: Optional[str] = None
    file_count: int = 0
    original_size: int = 0
    compressed_size: int = 0
    elapsed_seconds: float = 0.0
    error: Optional[str] = None
    error_details: Optional[str] = None
    cancelled: bool = False
    warnings: list[str] = field(default_factory=list)


@dataclass
class ArchiveEntry:
    """Thông tin một mục (file/thư mục) trong archive."""
    filename: str
    is_dir: bool
    file_size: int
    compress_size: int
    date_time: Optional[tuple] = None
    is_encrypted: bool = False
    crc: int = 0


@dataclass
class ArchiveMetadata:
    """Thông tin tổng quan về file ZIP."""
    file_path: str
    file_size: int
    total_entries: int = 0
    total_files: int = 0
    total_dirs: int = 0
    uncompressed_size: int = 0
    compressed_size: int = 0
    ratio_percent: float = 0.0
    is_encrypted: bool = False
    has_zip_bomb_risk: bool = False
    zip_bomb_warning: Optional[str] = None
