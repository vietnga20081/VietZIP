"""Helper cho cửa sổ phụ (Toplevel) và tài nguyên dùng chung (logo/icon có cache)."""

from __future__ import annotations

from functools import lru_cache
from typing import Optional

import customtkinter as ctk
from PIL import Image

from vietzip.utils.file_utils import get_asset_path


@lru_cache(maxsize=8)
def _load_logo_pil(px: int) -> Optional[Image.Image]:
    """Nạp icon-VietZIP.png một lần rồi thu nhỏ (file gốc 1254px, rất nặng nếu nạp lặp lại)."""
    path = get_asset_path("icon-VietZIP.png")
    if not path.exists():
        return None
    try:
        with Image.open(path) as im:
            im = im.convert("RGBA")
            im.thumbnail((px, px), Image.LANCZOS)
            return im.copy()
    except Exception:
        return None


_logo_cache: dict[int, Optional[ctk.CTkImage]] = {}


def get_logo_image(size: int) -> Optional[ctk.CTkImage]:
    """Logo VietZIP dạng CTkImage (cache theo kích thước). None nếu thiếu asset."""
    if size not in _logo_cache:
        pil = _load_logo_pil(size * 2)
        _logo_cache[size] = (
            ctk.CTkImage(light_image=pil, dark_image=pil, size=(size, size)) if pil else None
        )
    return _logo_cache[size]


def get_window_icon_pil() -> Optional[Image.Image]:
    return _load_logo_pil(256)


def apply_window_icon(window) -> None:
    """Gán icon .ico cho cửa sổ. CTkToplevel tự ghi đè icon sau ~200ms nên gán lại sau đó."""
    ico = get_asset_path("vietzip.ico")
    if not ico.exists():
        return

    def _set():
        try:
            if window.winfo_exists():
                window.iconbitmap(str(ico))
        except Exception:
            pass

    _set()
    try:
        window.after(250, _set)
    except Exception:
        pass


def bring_to_front(window: ctk.CTkToplevel, master=None) -> None:
    """Đảm bảo cửa sổ toplevel nổi lên phía trước master và nhận focus."""
    if master is not None and hasattr(master, "winfo_exists"):
        try:
            if master.winfo_exists():
                window.transient(master)
        except Exception:
            pass

    def _apply():
        try:
            if window.winfo_exists():
                window.deiconify()
                window.lift()
                window.attributes("-topmost", True)
                window.focus_force()
                window.after(120, _release)
        except Exception:
            pass

    def _release():
        try:
            if window.winfo_exists():
                window.attributes("-topmost", False)
                window.lift()
                window.focus_force()
        except Exception:
            pass

    _apply()
    try:
        window.after(60, _apply)
    except Exception:
        pass


def setup_toplevel_window(window: ctk.CTkToplevel, master=None, width: int = 540, height: int = 500) -> None:
    """Căn giữa theo master (hoặc màn hình), gán transient, icon, Esc để đóng, đưa lên trước."""
    try:
        if master is not None and hasattr(master, "winfo_exists") and master.winfo_exists():
            window.transient(master)
            master.update_idletasks()
            x = max(0, master.winfo_x() + (master.winfo_width() - width) // 2)
            y = max(0, master.winfo_y() + (master.winfo_height() - height) // 2)
        else:
            x = max(0, (window.winfo_screenwidth() - width) // 2)
            y = max(0, (window.winfo_screenheight() - height) // 2)
        window.geometry(f"{width}x{height}+{x}+{y}")
    except Exception:
        window.geometry(f"{width}x{height}")

    apply_window_icon(window)
    window.bind("<Escape>", lambda e: window.destroy(), add="+")
    bring_to_front(window, master)
