"""Archive inspection and metadata extraction."""

from __future__ import annotations

import zipfile
from pathlib import Path
from typing import Optional

try:
    import pyzipper
    HAS_PYZIPPER = True
except ImportError:
    HAS_PYZIPPER = False

from vietzip.core.models import ArchiveEntry, ArchiveMetadata
from vietzip.core.security import check_zip_bomb
from vietzip.utils.logging_utils import logger


def get_archive_metadata(
    zip_path: Path | str,
    max_bomb_uncompressed_bytes: int = 10 * 1024**3,
) -> ArchiveMetadata:
    """Đọc metadata tổng thể của file ZIP."""
    path = Path(zip_path)
    if not path.exists():
        raise FileNotFoundError(f"Không tìm thấy file: {zip_path}")

    file_size = path.stat().st_size
    has_bomb, bomb_msg = check_zip_bomb(path, max_uncompressed_bytes=max_bomb_uncompressed_bytes)

    total_entries = 0
    total_files = 0
    total_dirs = 0
    uncompressed_size = 0
    compressed_size = 0
    is_encrypted = False

    # Thử mở bằng pyzipper trước nếu có, hoặc zipfile chuẩn
    opener = pyzipper.AESZipFile if HAS_PYZIPPER else zipfile.ZipFile

    try:
        with opener(path, "r") as zf:
            for info in zf.infolist():
                total_entries += 1
                uncompressed_size += info.file_size
                compressed_size += info.compress_size

                # Kiểm tra cờ mã hóa (flag_bits & 0x1)
                if info.flag_bits & 0x1:
                    is_encrypted = True

                # Nhận diện thư mục (kết thúc bằng / hoặc attribute directory)
                if info.filename.endswith("/") or (info.external_attr >> 16) & 0o40000:
                    total_dirs += 1
                else:
                    total_files += 1

    except (zipfile.BadZipFile, Exception) as exc:
        logger.error("Lỗi khi đọc metadata file ZIP %s: %s", path.name, exc)
        raise

    ratio = 0.0
    if uncompressed_size > 0:
        ratio = max(0.0, (1.0 - (compressed_size / uncompressed_size))) * 100.0

    return ArchiveMetadata(
        file_path=str(path.resolve()),
        file_size=file_size,
        total_entries=total_entries,
        total_files=total_files,
        total_dirs=total_dirs,
        uncompressed_size=uncompressed_size,
        compressed_size=compressed_size,
        ratio_percent=ratio,
        is_encrypted=is_encrypted,
        has_zip_bomb_risk=has_bomb,
        zip_bomb_warning=bomb_msg if has_bomb else None,
    )


def list_archive_entries(zip_path: Path | str) -> list[ArchiveEntry]:
    """Lấy danh sách chi tiết các file/thư mục trong ZIP."""
    path = Path(zip_path)
    if not path.exists():
        raise FileNotFoundError(f"Không tìm thấy file: {zip_path}")

    opener = pyzipper.AESZipFile if HAS_PYZIPPER else zipfile.ZipFile
    entries: list[ArchiveEntry] = []

    with opener(path, "r") as zf:
        for info in zf.infolist():
            is_dir = info.filename.endswith("/") or bool((info.external_attr >> 16) & 0o40000)
            is_enc = bool(info.flag_bits & 0x1)
            entries.append(
                ArchiveEntry(
                    filename=info.filename,
                    is_dir=is_dir,
                    file_size=info.file_size,
                    compress_size=info.compress_size,
                    date_time=info.date_time,
                    is_encrypted=is_enc,
                    crc=info.CRC,
                )
            )

    return entries
