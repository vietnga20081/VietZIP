"""Unit tests for compressor."""

import threading
from pathlib import Path
import pytest
import zipfile

from vietzip.core.compressor import compress_archive
from vietzip.core.models import ProgressInfo


def test_compress_single_file(tmp_path):
    f = tmp_path / "hello.txt"
    f.write_text("VietZIP Xin Chào!", encoding="utf-8")

    out_zip = tmp_path / "out.zip"
    res = compress_archive([f], out_zip, level=6)

    assert res.success is True
    assert out_zip.exists()
    assert res.file_count == 1
    assert res.original_size > 0

    with zipfile.ZipFile(out_zip, "r") as zf:
        assert "hello.txt" in zf.namelist()
        assert zf.read("hello.txt").decode("utf-8") == "VietZIP Xin Chào!"


def test_compress_nested_folder_with_unicode(tmp_path):
    folder = tmp_path / "Dữ liệu tiếng Việt 🎯"
    folder.mkdir()

    sub = folder / "Thư mục con"
    sub.mkdir()

    f1 = folder / "tài_liệu_1.txt"
    f1.write_text("Nội dung tiếng Việt có dấu", encoding="utf-8")

    f2 = sub / "báo cáo tài chính.csv"
    f2.write_text("a,b,c\n1,2,3", encoding="utf-8")

    empty_sub = folder / "Thư mục rỗng"
    empty_sub.mkdir()

    out_zip = tmp_path / "vietnamese.zip"
    res = compress_archive([folder], out_zip, level=6)

    assert res.success is True
    assert out_zip.exists()

    with zipfile.ZipFile(out_zip, "r") as zf:
        names = zf.namelist()
        assert any("tài_liệu_1.txt" in n for n in names)
        assert any("báo cáo tài chính.csv" in n for n in names)
        assert any("Thư mục rỗng" in n for n in names)


def test_compress_cancel(tmp_path):
    f = tmp_path / "large_data.bin"
    f.write_bytes(b"0" * (1024 * 1024 * 5))  # 5 MB

    out_zip = tmp_path / "cancelled.zip"
    cancel_event = threading.Event()
    cancel_event.set()  # Cancel ngay lập tức

    res = compress_archive([f], out_zip, cancel_event=cancel_event)

    assert res.success is False
    assert res.cancelled is True
    assert not out_zip.exists()
    assert not (tmp_path / "cancelled.zip.tmp").exists()


def test_compress_with_password(tmp_path):
    f = tmp_path / "secret.txt"
    f.write_text("Dữ liệu tuyệt mật!", encoding="utf-8")

    out_zip = tmp_path / "encrypted.zip"
    res = compress_archive([f], out_zip, password="MySecretPassword123")

    assert res.success is True
    assert out_zip.exists()


def test_compress_zero_byte_file(tmp_path):
    f = tmp_path / "empty.txt"
    f.touch()

    out_zip = tmp_path / "empty.zip"
    res = compress_archive([f], out_zip)

    assert res.success is True
    assert out_zip.exists()
    with zipfile.ZipFile(out_zip, "r") as zf:
        assert "empty.txt" in zf.namelist()
        assert zf.read("empty.txt") == b""


def test_compress_duplicate_inputs(tmp_path):
    f = tmp_path / "dup.txt"
    f.write_text("Không trùng lặp", encoding="utf-8")

    out_zip = tmp_path / "dedup.zip"
    # Truyền cùng 1 file 3 lần
    res = compress_archive([f, f, f], out_zip)

    assert res.success is True
    assert res.file_count == 1
    with zipfile.ZipFile(out_zip, "r") as zf:
        assert len(zf.namelist()) == 1

