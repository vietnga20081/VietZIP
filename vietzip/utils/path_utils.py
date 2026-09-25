"""Gợi ý & kiểm tra đường dẫn đầu ra (thuần logic, không phụ thuộc UI nên dễ test)."""

from __future__ import annotations

import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional

from vietzip.utils.file_utils import generate_unique_dest_path

_WIN_INVALID = re.compile(r'[<>:"/\\|?*]')


def _clean_name(name: str) -> str:
    name = _WIN_INVALID.sub("_", name).strip().rstrip(". ")
    return name or "Archive"


def suggest_zip_name(sources: Iterable[str], behavior: str = "smart") -> str:
    """Tên ZIP gợi ý. behavior: 'smart' (theo nguồn) | 'timestamp' (VietZIP_ngày_giờ)."""
    srcs = [Path(s) for s in sources]
    if behavior == "timestamp" or not srcs:
        return f"VietZIP_{datetime.now():%Y%m%d_%H%M%S}.zip"
    if len(srcs) == 1:
        s = srcs[0]
        base = s.name if s.is_dir() else (s.stem or s.name)
        return f"{_clean_name(base)}.zip"
    parents = {str(s.parent) for s in srcs}
    if len(parents) == 1:
        parent_name = srcs[0].parent.name
        if parent_name:
            return f"{_clean_name(parent_name)}.zip"
    return "Archive.zip"


def suggest_output_path(
    sources: list[str], base_dir: Optional[str] = None, behavior: str = "smart"
) -> str:
    """Đường dẫn ZIP đầy đủ, tự tránh trùng tên file có sẵn."""
    if not sources:
        return ""
    folder = Path(base_dir) if base_dir else Path(sources[0]).parent
    return str(generate_unique_dest_path(folder / suggest_zip_name(sources, behavior)))


def normalize_zip_output(path: str) -> str:
    """Bảo đảm đuôi .zip."""
    path = path.strip()
    if path and not path.lower().endswith(".zip"):
        path += ".zip"
    return path


def existing_ancestor(path: Path) -> Optional[Path]:
    """Thư mục cha gần nhất đã tồn tại."""
    p = path
    while True:
        if p.exists():
            return p if p.is_dir() else p.parent
        if p == p.parent:
            return None
        p = p.parent


def _is_inside(child: Path, parent: Path) -> bool:
    try:
        child.relative_to(parent)
        return True
    except ValueError:
        return False


def validate_output_zip(output: str, sources: Iterable[str]) -> tuple[Optional[str], Optional[str]]:
    """Trả về (lỗi, cảnh báo). Có lỗi => không được phép chạy."""
    output = output.strip()
    if not output:
        return "Hãy chọn nơi lưu file ZIP.", None

    p = Path(normalize_zip_output(output))
    if p.is_dir():
        return "Đường dẫn này là một thư mục. Hãy nhập tên file ZIP.", None
    if sys.platform == "win32" and _WIN_INVALID.search(p.name):
        return 'Tên file không được chứa các ký tự  < > : " / \\ | ? *', None

    ancestor = existing_ancestor(p.parent)
    if ancestor is None:
        return "Thư mục lưu không hợp lệ.", None
    if not os.access(ancestor, os.W_OK):
        return "Không có quyền ghi vào thư mục này. Hãy chọn thư mục khác.", None

    resolved = p.resolve()
    for s in sources:
        sp = Path(s).resolve()
        if sp == resolved:
            return "File ZIP đầu ra trùng với file nguồn.", None
        if sp.is_dir() and _is_inside(resolved, sp):
            return "Không thể lưu file ZIP bên trong chính thư mục đang nén.", None

    if p.exists():
        return None, "File đã tồn tại và sẽ bị ghi đè."
    if not p.parent.exists():
        return None, "Thư mục chưa tồn tại, sẽ được tạo tự động."
    return None, None


def suggest_extract_dir(zip_path: str, create_subfolder: bool = True, base_dir: Optional[str] = None) -> str:
    z = Path(zip_path)
    base = Path(base_dir) if base_dir else z.parent
    return str(base / _clean_name(z.stem)) if create_subfolder else str(base)


def validate_dest_dir(dest: str) -> tuple[Optional[str], Optional[str]]:
    """Trả về (lỗi, cảnh báo) cho thư mục giải nén."""
    dest = dest.strip()
    if not dest:
        return "Hãy chọn nơi giải nén.", None
    p = Path(dest)
    if p.exists() and not p.is_dir():
        return "Đường dẫn này là một file, không phải thư mục.", None
    ancestor = existing_ancestor(p)
    if ancestor is None:
        return "Thư mục giải nén không hợp lệ.", None
    if not os.access(ancestor, os.W_OK):
        return "Không có quyền ghi vào thư mục này. Hãy chọn thư mục khác.", None
    if not p.exists():
        return None, "Thư mục chưa tồn tại, sẽ được tạo khi giải nén."
    return None, None


_DND_TOKEN = re.compile(r"\{([^}]*)\}|(\S+)")


def parse_dropped_paths(data: str, splitlist=None) -> list[str]:
    """Tách chuỗi kéo-thả của TkDnD thành danh sách đường dẫn.

    - Đường dẫn có khoảng trắng được TkDnD bọc trong {} (cả Unicode).
    - Ưu tiên `tk.splitlist` (chuẩn Tcl); nếu lỗi/không có thì dùng regex.
    - Dữ liệu lỗi/rác trả về danh sách rỗng, không bao giờ ném exception.
    """
    if not data or not isinstance(data, str):
        return []
    tokens: list[str] = []
    try:
        if splitlist is not None:
            tokens = [str(t) for t in splitlist(data)]
    except Exception:
        tokens = []
    if not tokens:
        tokens = [a or b for a, b in _DND_TOKEN.findall(data)]
    out: list[str] = []
    for t in tokens:
        t = t.strip().strip("\x00")
        if t:
            out.append(os.path.normpath(t))
    return out
