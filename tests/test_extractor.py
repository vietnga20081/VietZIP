"""Unit tests for extractor."""

import pytest
import zipfile
from pathlib import Path

from vietzip.core.compressor import compress_archive
from vietzip.core.extractor import extract_archive, extract_selected
from vietzip.core.models import OverwritePolicy


def test_extract_archive_basic(tmp_path):
    # Chuẩn bị file zip
    src_file = tmp_path / "sample.txt"
    src_file.write_text("Dữ liệu thử nghiệm VietZIP", encoding="utf-8")

    zip_file = tmp_path / "test.zip"
    compress_archive([src_file], zip_file)

    # Giải nén
    dest_dir = tmp_path / "extracted"
    res = extract_archive(zip_file, dest_dir)

    assert res.success is True
    assert (dest_dir / "sample.txt").exists()
    assert (dest_dir / "sample.txt").read_text(encoding="utf-8") == "Dữ liệu thử nghiệm VietZIP"


def test_extract_overwrite_policy_auto_rename(tmp_path):
    src_file = tmp_path / "report.txt"
    src_file.write_text("Phiên bản mới", encoding="utf-8")

    zip_file = tmp_path / "test_ow.zip"
    compress_archive([src_file], zip_file)

    dest_dir = tmp_path / "extracted_ow"
    dest_dir.mkdir()

    existing = dest_dir / "report.txt"
    existing.write_text("Phiên bản cũ đã có", encoding="utf-8")

    # Giải nén với auto_rename
    res = extract_archive(zip_file, dest_dir, overwrite_policy=OverwritePolicy.AUTO_RENAME)
    assert res.success is True

    # File cũ không bị đè
    assert existing.read_text(encoding="utf-8") == "Phiên bản cũ đã có"
    # Tự sinh tên mới report (1).txt
    renamed = dest_dir / "report (1).txt"
    assert renamed.exists()
    assert renamed.read_text(encoding="utf-8") == "Phiên bản mới"


def test_extract_overwrite_policy_overwrite(tmp_path):
    src_file = tmp_path / "report2.txt"
    src_file.write_text("Ghi đè thành công!", encoding="utf-8")

    zip_file = tmp_path / "test_ow2.zip"
    compress_archive([src_file], zip_file)

    dest_dir = tmp_path / "extracted_ow2"
    dest_dir.mkdir()

    existing = dest_dir / "report2.txt"
    existing.write_text("Nội dung cũ", encoding="utf-8")

    res = extract_archive(zip_file, dest_dir, overwrite_policy=OverwritePolicy.OVERWRITE)
    assert res.success is True
    assert existing.read_text(encoding="utf-8") == "Ghi đè thành công!"


def test_extract_with_password(tmp_path):
    src_file = tmp_path / "top_secret.txt"
    src_file.write_text("Mật khẩu giải nén thành công!", encoding="utf-8")

    zip_file = tmp_path / "locked.zip"
    compress_archive([src_file], zip_file, password="Secr3tPassword!")

    dest_dir = tmp_path / "unlocked"
    res = extract_archive(zip_file, dest_dir, password="Secr3tPassword!")
    assert res.success is True
    assert (dest_dir / "top_secret.txt").exists()
    assert (dest_dir / "top_secret.txt").read_text(encoding="utf-8") == "Mật khẩu giải nén thành công!"


def test_extract_cancel(tmp_path):
    import threading
    src_file = tmp_path / "data.bin"
    src_file.write_bytes(b"A" * 1024 * 1024)

    zip_file = tmp_path / "cancel.zip"
    compress_archive([src_file], zip_file)

    cancel_event = threading.Event()
    cancel_event.set()

    dest_dir = tmp_path / "out_cancel"
    res = extract_archive(zip_file, dest_dir, cancel_event=cancel_event)
    assert res.success is False
    assert res.cancelled is True


def test_extract_corrupt_zip(tmp_path):
    bad_zip = tmp_path / "corrupt.zip"
    bad_zip.write_bytes(b"This is definitely not a zip file")

    dest_dir = tmp_path / "out_bad"
    res = extract_archive(bad_zip, dest_dir)
    assert res.success is False
    assert res.error is not None



def test_extract_cancel_mid_file_removes_partial(tmp_path):
    import threading

    src = tmp_path / "big.bin"
    src.write_bytes(b"y" * (4 * 1024 * 1024))
    z = tmp_path / "big.zip"
    with zipfile.ZipFile(z, "w", zipfile.ZIP_STORED) as zf:
        zf.write(src, "big.bin")
    dest = tmp_path / "out"
    ev = threading.Event()

    res = extract_archive(z, dest, cancel_event=ev, progress_callback=lambda _i: ev.set(), chunk_size=64 * 1024)
    assert res.cancelled is True
    assert not (dest / "big.bin").exists()


def test_extract_selected_only_extracts_chosen_members(tmp_path):
    """v2.1: giải nén chọn lọc — chỉ các entry được chỉ định mới xuất hiện ở đích."""
    src_dir = tmp_path / "src"
    (src_dir / "sub").mkdir(parents=True)
    (src_dir / "a.txt").write_text("A")
    (src_dir / "b.txt").write_text("B")
    (src_dir / "sub" / "c.txt").write_text("C")

    z = tmp_path / "test.zip"
    with zipfile.ZipFile(z, "w") as zf:
        zf.write(src_dir / "a.txt", "a.txt")
        zf.write(src_dir / "b.txt", "b.txt")
        zf.write(src_dir / "sub" / "c.txt", "sub/c.txt")

    dest = tmp_path / "out"
    res = extract_selected(z, dest, members=["b.txt", "sub/c.txt"])

    assert res.success is True
    assert res.file_count == 2
    assert not (dest / "a.txt").exists()
    assert (dest / "b.txt").read_text() == "B"
    assert (dest / "sub" / "c.txt").read_text() == "C"


def test_extract_selected_empty_members_returns_error(tmp_path):
    src = tmp_path / "a.txt"
    src.write_text("A")
    z = tmp_path / "test.zip"
    with zipfile.ZipFile(z, "w") as zf:
        zf.write(src, "a.txt")

    res = extract_selected(z, tmp_path / "out", members=["khong_ton_tai.txt"])
    assert res.success is False
    assert res.cancelled is False
