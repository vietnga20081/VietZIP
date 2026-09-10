"""Security modules for VietZIP: safe path extraction and zip bomb detection."""

from __future__ import annotations

import os
import zipfile
from pathlib import Path


class SecurityError(Exception):
    """Lỗi bảo mật khi thao tác với file ZIP."""
    pass


def sanitize_member_name(member_name: str) -> str:
    """Loại bỏ ký tự nguy hiểm, drive letter, leading slashes."""
    clean_name = member_name.replace("\\", "/").strip()
    # Loại bỏ drive prefix như C:
    if len(clean_name) >= 2 and clean_name[1] == ":" and clean_name[0].isalpha():
        clean_name = clean_name[2:]
    # Loại bỏ leading slashes
    clean_name = clean_name.lstrip("/")
    return clean_name


def safe_extract_path(base_dir: Path | str, member_name: str) -> Path:
    """
    Xác định đường dẫn an toàn để giải nén file.
    Chống tấn công Path Traversal / Zip Slip.
    Nếu file muốn ghi đè ra ngoài base_dir -> Ném ngoại lệ SecurityError.
    """
    base = Path(base_dir).resolve()
    clean_name = sanitize_member_name(member_name)

    if "\x00" in clean_name:
        raise SecurityError(f"Phát hiện ký tự NULL trong tên file: {member_name!r}")

    # Tạo đường dẫn mục tiêu và chuẩn hóa
    target = (base / clean_name).resolve()

    try:
        # Kiểm tra xem target có phải là con của base không
        target.relative_to(base)
    except ValueError:
        raise SecurityError(
            f"Phát hiện nguy cơ Zip Slip / Path Traversal: "
            f"Mục '{member_name}' cố gắng ghi ra ngoài thư mục đích!"
        )

    return target


def is_safe_path(base_dir: Path | str, member_name: str) -> bool:
    """Kiểm tra nhanh xem member_name có an toàn hay không."""
    try:
        safe_extract_path(base_dir, member_name)
        return True
    except SecurityError:
        return False


def check_zip_bomb(
    zip_path: Path | str,
    max_ratio: float = 50.0,
    max_uncompressed_bytes: int = 10 * 1024**3,  # 10 GB
) -> tuple[bool, str]:
    """
    Kiểm tra xem file ZIP có nguy cơ là Zip Bomb hay không.
    Trả về (has_risk, reason).
    """
    path = Path(zip_path)
    if not path.exists():
        return False, "File không tồn tại."

    compressed_file_size = path.stat().st_size
    if compressed_file_size == 0:
        return False, ""

    try:
        with zipfile.ZipFile(path, "r") as zf:
            total_uncompressed = 0
            for info in zf.infolist():
                total_uncompressed += info.file_size

            ratio = total_uncompressed / max(compressed_file_size, 1)

            if total_uncompressed > max_uncompressed_bytes and ratio > max_ratio:
                return True, (
                    f"Tỷ lệ nén bất thường ({ratio:.1f}:1) và dung lượng giải nén dự kiến "
                    f"lên tới {total_uncompressed / (1024**3):.1f} GB. Có thể là Zip Bomb!"
                )
            elif ratio > 100.0 and total_uncompressed > 1024 * 1024 * 100:  # > 100MB uncompressed & > 100:1 ratio
                return True, (
                    f"Tỷ lệ nén cực cao ({ratio:.1f}:1). File ZIP dung lượng nhỏ "
                    f"nhưng giải nén ra rất lớn ({total_uncompressed / (1024**2):.1f} MB)."
                )

    except Exception:
        # Nếu không mở được thì không phải zip bomb hoặc zip hỏng
        return False, ""

    return False, ""
