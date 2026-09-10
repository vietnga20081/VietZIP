"""File system and OS helper utilities."""

from __future__ import annotations

import os
import sys
import shutil
import subprocess
from pathlib import Path
from typing import Generator, Iterable, Optional


def get_asset_path(filename: str) -> Path:
    """Tìm đường dẫn tệp tài nguyên hoạt động tin cậy trong cả môi trường dev và frozen PyInstaller."""
    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            c1 = Path(meipass) / "assets" / filename
            if c1.exists():
                return c1
            c1_direct = Path(meipass) / filename
            if c1_direct.exists():
                return c1_direct
        exe_dir = Path(sys.executable).parent
        c2 = exe_dir / "assets" / filename
        if c2.exists():
            return c2
        c2_int = exe_dir / "_internal" / "assets" / filename
        if c2_int.exists():
            return c2_int

    dev_path = Path(__file__).resolve().parent.parent.parent / "assets" / filename
    if dev_path.exists():
        return dev_path
    return Path(__file__).resolve().parent.parent.parent / filename


def get_available_disk_space(path: Path | str) -> int:
    """Lấy dung lượng trống khả dụng (bytes) tại ổ đĩa chứa path."""
    try:
        p = Path(path).resolve()
        # Nếu đường dẫn chưa tồn tại, lấy thư mục cha gần nhất tồn tại
        while not p.exists() and p != p.parent:
            p = p.parent
        usage = shutil.disk_usage(p)
        return usage.free
    except Exception:
        return -1


def open_in_explorer(target_path: Path | str) -> bool:
    """Mở thư mục chứa file hoặc mở chính thư mục đó trong Explorer / Finder."""
    try:
        p = Path(target_path).resolve()
        if not p.exists():
            return False

        if sys.platform == "win32":
            if p.is_file():
                # Chọn file trong explorer
                subprocess.run(f'explorer /select,"{p}"', shell=True, check=False)
            else:
                os.startfile(str(p))
            return True
        elif sys.platform == "darwin":
            subprocess.run(["open", "-R" if p.is_file() else "", str(p)], check=False)
            return True
        else:
            folder = p.parent if p.is_file() else p
            subprocess.run(["xdg-open", str(folder)], check=False)
            return True
    except Exception:
        return False


def open_file(file_path: Path | str) -> bool:
    """Mở file bằng ứng dụng mặc định của hệ điều hành."""
    try:
        p = Path(file_path).resolve()
        if not p.exists():
            return False

        if sys.platform == "win32":
            os.startfile(str(p))
            return True
        elif sys.platform == "darwin":
            subprocess.run(["open", str(p)], check=False)
            return True
        else:
            subprocess.run(["xdg-open", str(p)], check=False)
            return True
    except Exception:
        return False


def generate_unique_dest_path(target_path: Path | str) -> Path:
    """
    Nếu file/thư mục đã tồn tại, tự sinh tên mới theo quy tắc:
    file.txt -> file (1).txt, file (2).txt, ...
    """
    path = Path(target_path)
    if not path.exists():
        return path

    parent = path.parent
    stem = path.stem
    suffix = path.suffix

    counter = 1
    while True:
        candidate = parent / f"{stem} ({counter}){suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def collect_items_to_compress(
    sources: Iterable[Path | str],
) -> tuple[list[tuple[Path, Path, int]], int, int, int]:
    """
    Thu thập danh sách tất cả file/thư mục rỗng cần nén.
    Chống trùng lặp (duplicate detection) nếu cùng file được thêm nhiều lần
    hoặc file nằm trong folder đã được chọn.

    Trả về:
        (entries, total_bytes, total_files, total_dirs)
        trong đó mỗi entry là (full_path, arcname, file_size)
    """
    seen_paths: set[Path] = set()
    entries: list[tuple[Path, Path, int]] = []
    total_bytes = 0
    total_files = 0
    total_dirs = 0

    resolved_sources = [Path(s).resolve() for s in sources if Path(s).exists()]

    for p in resolved_sources:
        if p.is_file():
            if p in seen_paths:
                continue
            seen_paths.add(p)
            try:
                size = p.stat().st_size
            except OSError:
                size = 0
            entries.append((p, Path(p.name), size))
            total_bytes += size
            total_files += 1

        elif p.is_dir():
            base_parent = p.parent
            for root, dirs, files in os.walk(p):
                root_path = Path(root)
                # Xử lý thư mục rỗng để lưu giữ cấu trúc trong ZIP
                if not dirs and not files:
                    if root_path not in seen_paths:
                        seen_paths.add(root_path)
                        arcname = root_path.relative_to(base_parent)
                        entries.append((root_path, arcname, 0))
                        total_dirs += 1

                for f in files:
                    full_file = root_path / f
                    if full_file in seen_paths:
                        continue
                    seen_paths.add(full_file)
                    try:
                        size = full_file.stat().st_size
                    except OSError:
                        size = 0
                    arcname = full_file.relative_to(base_parent)
                    entries.append((full_file, arcname, size))
                    total_bytes += size
                    total_files += 1

    return entries, total_bytes, total_files, total_dirs
