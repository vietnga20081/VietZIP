"""Windows Explorer context menu integration service using winreg."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional

from vietzip.utils.logging_utils import logger


def notify_shell_icon_change():
    """Gửi thông báo SHChangeNotify buộc Windows Shell làm mới toàn bộ Icon Cache."""
    if sys.platform == "win32":
        try:
            import ctypes
            # SHCNE_ASSOCCHANGED = 0x08000000, SHCNF_IDLIST = 0
            ctypes.windll.shell32.SHChangeNotify(0x08000000, 0, None, None)
        except Exception as e:
            logger.debug("SHChangeNotify error: %s", e)


def find_best_icon_path(target_exe: Optional[Path | str] = None) -> str:
    """
    Tìm đường dẫn tệp .ico trực tiếp để Windows Explorer đọc ngay lập tức,
    hoàn toàn tránh được bộ đệm icon PE cũ của hệ điều hành.
    """
    candidates: list[Path] = []
    if target_exe:
        base_dir = Path(target_exe).resolve().parent
        candidates.extend([
            base_dir / "vietzip.ico",
            base_dir / "assets" / "vietzip.ico",
            base_dir / "_internal" / "assets" / "vietzip.ico",
        ])
    if getattr(sys, "frozen", False):
        base_dir = Path(sys.executable).resolve().parent
        candidates.extend([
            base_dir / "vietzip.ico",
            base_dir / "assets" / "vietzip.ico",
            base_dir / "_internal" / "assets" / "vietzip.ico",
        ])
    # Trong môi trường phát triển / repo
    root_dir = Path(__file__).resolve().parent.parent.parent
    candidates.extend([
        root_dir / "assets" / "vietzip.ico",
        root_dir / "vietzip.ico",
    ])
    for c in candidates:
        if c.exists():
            return f'"{c.resolve()}"'

    exe = str(target_exe) if target_exe else sys.executable
    return f'"{Path(exe).resolve()}",0'


def get_default_exe_command() -> tuple[str, str]:
    """
    Xác định đường dẫn thực thi và icon phù hợp.
    Trả về (command_prefix, icon_path).
    """
    if getattr(sys, "frozen", False):
        exe = sys.executable
        return f'"{exe}"', find_best_icon_path(exe)
    else:
        python_exe = sys.executable
        # Dùng pythonw nếu có để không hiện console đen khi click chuột phải
        pythonw_candidate = Path(python_exe).parent / "pythonw.exe"
        py_runner = str(pythonw_candidate) if pythonw_candidate.exists() else python_exe

        main_script = Path(__file__).resolve().parent.parent.parent / "main.py"
        icon_str = find_best_icon_path()

        return f'"{py_runner}" "{main_script}"', icon_str


def is_context_menu_registered() -> bool:
    """Kiểm tra xem menu chuột phải VietZIP đã được đăng ký trong Windows Registry chưa."""
    if sys.platform != "win32":
        return False

    import winreg

    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Classes\*\shell\VietZIP.Compress",
            0,
            winreg.KEY_READ,
        )
        winreg.CloseKey(key)
        return True
    except OSError:
        return False


def register_context_menu(custom_exe_path: Optional[str] = None) -> tuple[bool, str]:
    """
    Đăng ký menu chuột phải trong Windows Explorer:
    1. Chuột phải vào bất kỳ file nào: 'Nén bằng VietZIP'
    2. Chuột phải vào bất kỳ thư mục nào: 'Nén bằng VietZIP'
    3. Chuột phải vào file .zip: 'Giải nén bằng VietZIP'
    """
    if sys.platform != "win32":
        return False, "Tính năng chỉ hỗ trợ trên hệ điều hành Windows."

    import winreg

    try:
        if custom_exe_path and Path(custom_exe_path).exists():
            cmd_prefix = f'"{Path(custom_exe_path).resolve()}"'
            icon_path = find_best_icon_path(custom_exe_path)
        else:
            cmd_prefix, icon_path = get_default_exe_command()

        # 1. Menu nén cho tất cả các file (*\shell\VietZIP.Compress)
        file_key_path = r"Software\Classes\*\shell\VietZIP.Compress"
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, file_key_path) as k:
            winreg.SetValueEx(k, "", 0, winreg.REG_SZ, "Nén bằng VietZIP")
            winreg.SetValueEx(k, "Icon", 0, winreg.REG_SZ, icon_path)
            winreg.SetValueEx(k, "MultiSelectModel", 0, winreg.REG_SZ, "Document")
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, rf"{file_key_path}\command") as k:
            winreg.SetValueEx(k, "", 0, winreg.REG_SZ, f'{cmd_prefix} compress "%1"')

        # 2. Menu nén cho thư mục (Directory\shell\VietZIP.Compress)
        dir_key_path = r"Software\Classes\Directory\shell\VietZIP.Compress"
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, dir_key_path) as k:
            winreg.SetValueEx(k, "", 0, winreg.REG_SZ, "Nén bằng VietZIP")
            winreg.SetValueEx(k, "Icon", 0, winreg.REG_SZ, icon_path)
            winreg.SetValueEx(k, "MultiSelectModel", 0, winreg.REG_SZ, "Document")
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, rf"{dir_key_path}\command") as k:
            winreg.SetValueEx(k, "", 0, winreg.REG_SZ, f'{cmd_prefix} compress "%V"')

        # 3. Menu nén nền thư mục hiện tại (Directory\Background\shell\VietZIP.Compress)
        bg_key_path = r"Software\Classes\Directory\Background\shell\VietZIP.Compress"
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, bg_key_path) as k:
            winreg.SetValueEx(k, "", 0, winreg.REG_SZ, "Nén thư mục này bằng VietZIP")
            winreg.SetValueEx(k, "Icon", 0, winreg.REG_SZ, icon_path)
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, rf"{bg_key_path}\command") as k:
            winreg.SetValueEx(k, "", 0, winreg.REG_SZ, f'{cmd_prefix} compress "%V"')

        # 4. Menu giải nén cho file .zip (SystemFileAssociations\.zip\shell\VietZIP.Extract)
        zip_key_path = r"Software\Classes\SystemFileAssociations\.zip\shell\VietZIP.Extract"
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, zip_key_path) as k:
            winreg.SetValueEx(k, "", 0, winreg.REG_SZ, "Giải nén bằng VietZIP")
            winreg.SetValueEx(k, "Icon", 0, winreg.REG_SZ, icon_path)
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, rf"{zip_key_path}\command") as k:
            winreg.SetValueEx(k, "", 0, winreg.REG_SZ, f'{cmd_prefix} extract "%1"')

        # Báo cho Windows Shell cập nhật icon cache tức thì
        notify_shell_icon_change()

        logger.info("Đã đăng ký menu chuột phải Windows thành công với icon: %s", icon_path)
        return True, "Đã thêm VietZIP vào menu chuột phải thành công!"

    except Exception as exc:
        logger.exception("Lỗi đăng ký menu chuột phải: %s", exc)
        return False, f"Không thể đăng ký menu chuột phải: {exc}"


def unregister_context_menu() -> tuple[bool, str]:
    """Gỡ bỏ các khóa menu chuột phải VietZIP trong Registry."""
    if sys.platform != "win32":
        return False, "Tính năng chỉ hỗ trợ trên hệ điều hành Windows."

    import winreg

    def _delete_key_tree(root, subkey):
        try:
            hkey = winreg.OpenKey(root, subkey, 0, winreg.KEY_ALL_ACCESS)
        except OSError:
            return
        try:
            while True:
                child = winreg.EnumKey(hkey, 0)
                _delete_key_tree(hkey, child)
        except OSError:
            pass
        winreg.CloseKey(hkey)
        try:
            winreg.DeleteKey(root, subkey)
        except OSError:
            pass

    try:
        _delete_key_tree(winreg.HKEY_CURRENT_USER, r"Software\Classes\*\shell\VietZIP.Compress")
        _delete_key_tree(winreg.HKEY_CURRENT_USER, r"Software\Classes\Directory\shell\VietZIP.Compress")
        _delete_key_tree(winreg.HKEY_CURRENT_USER, r"Software\Classes\Directory\Background\shell\VietZIP.Compress")
        _delete_key_tree(winreg.HKEY_CURRENT_USER, r"Software\Classes\SystemFileAssociations\.zip\shell\VietZIP.Extract")

        notify_shell_icon_change()
        logger.info("Đã gỡ bỏ menu chuột phải VietZIP.")
        return True, "Đã gỡ bỏ VietZIP khỏi menu chuột phải."
    except Exception as exc:
        logger.exception("Lỗi khi gỡ menu chuột phải: %s", exc)
        return False, f"Không thể gỡ bỏ: {exc}"
