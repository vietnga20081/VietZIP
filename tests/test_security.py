"""Unit tests for security: Zip Slip and Zip Bomb prevention."""

import pytest
import zipfile
from pathlib import Path

from vietzip.core.security import (
    SecurityError,
    check_zip_bomb,
    is_safe_path,
    safe_extract_path,
)


def test_safe_extract_path_valid(tmp_path):
    dest = tmp_path / "output"
    dest.mkdir()

    # File bình thường
    p1 = safe_extract_path(dest, "document.txt")
    assert p1 == dest / "document.txt"

    # Thư mục con bình thường
    p2 = safe_extract_path(dest, "subfolder/image.png")
    assert p2 == dest / "subfolder" / "image.png"

    # Đường dẫn lồng nhau
    p3 = safe_extract_path(dest, "a/b/c/d.txt")
    assert p3 == dest / "a" / "b" / "c" / "d.txt"


def test_safe_extract_path_zip_slip_traversal(tmp_path):
    dest = tmp_path / "output"
    dest.mkdir()

    # Cố tình nhảy ra ngoài bằng ../
    with pytest.raises(SecurityError):
        safe_extract_path(dest, "../evil.exe")

    with pytest.raises(SecurityError):
        safe_extract_path(dest, "../../windows/system32/cmd.exe")

    with pytest.raises(SecurityError):
        safe_extract_path(dest, "sub/../../outside.txt")


def test_safe_extract_path_null_byte(tmp_path):
    dest = tmp_path / "output"
    dest.mkdir()

    with pytest.raises(SecurityError):
        safe_extract_path(dest, "evil.txt\x00.exe")


def test_is_safe_path(tmp_path):
    dest = tmp_path / "output"
    assert is_safe_path(dest, "safe.txt") is True
    assert is_safe_path(dest, "../unsafe.txt") is False


def test_check_zip_bomb(tmp_path):
    zip_file = tmp_path / "normal.zip"
    with zipfile.ZipFile(zip_file, "w") as zf:
        zf.writestr("test.txt", "Hello World" * 10)

    has_risk, msg = check_zip_bomb(zip_file)
    assert has_risk is False
