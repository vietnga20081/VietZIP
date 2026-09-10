"""VietZIP Setup Wizard (Windows Installer)."""

from __future__ import annotations

import os
import sys
import shutil
import zipfile
import threading
import subprocess
import winreg
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

# Thiết lập theme cho Installer
ctk.set_appearance_mode("Light")
ctk.set_default_color_theme("green")

APP_NAME = "VietZIP"
APP_VERSION = "2.0.0"
PUBLISHER = "VietZIP Team"

COLOR_TEXT_PRIMARY = "#0F172A"
COLOR_TEXT_SECONDARY = "#334155"
COLOR_BORDER = "#E2E8F0"
COLOR_CARD = "#FFFFFF"
FONT_TITLE = ("Segoe UI", 20, "bold")
FONT_SECTION = ("Segoe UI", 13, "bold")
FONT_REGULAR = ("Segoe UI", 12)
FONT_SMALL = ("Segoe UI", 10)


def create_windows_shortcut(
    shortcut_path: Path | str,
    target_path: Path | str,
    icon_path: Path | str | None = None,
    working_dir: Path | str | None = None,
):
    """Tạo shortcut .lnk trên Windows bằng VBScript tiêu chuẩn."""
    s_path = str(Path(shortcut_path).resolve())
    t_path = str(Path(target_path).resolve())
    i_path = str(Path(icon_path).resolve()) if icon_path else t_path
    w_path = str(Path(working_dir).resolve()) if working_dir else str(Path(target_path).parent.resolve())

    vbs_content = f"""
Set oWS = WScript.CreateObject("WScript.Shell")
Set oLink = oWS.CreateShortcut("{s_path}")
oLink.TargetPath = "{t_path}"
oLink.IconLocation = "{i_path},0"
oLink.WorkingDirectory = "{w_path}"
oLink.Save
"""
    vbs_file = Path(os.environ.get("TEMP", ".")) / f"vietzip_lnk_{os.getpid()}.vbs"
    try:
        with open(vbs_file, "w", encoding="ascii", errors="ignore") as fp:
            fp.write(vbs_content)
        subprocess.run(["cscript", "//nologo", str(vbs_file)], check=True, creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0)
    finally:
        if vbs_file.exists():
            try:
                vbs_file.unlink()
            except Exception:
                pass


def register_uninstall_info(install_dir: Path, version: str = APP_VERSION):
    """Đăng ký thông tin gỡ cài đặt vào Windows Settings / Control Panel."""
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\VietZIP"
    exe_path = install_dir / "VietZIP.exe"
    uninstaller_path = install_dir / "uninstall.bat"

    try:
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path) as k:
            winreg.SetValueEx(k, "DisplayName", 0, winreg.REG_SZ, f"VietZIP {version}")
            winreg.SetValueEx(k, "DisplayVersion", 0, winreg.REG_SZ, version)
            winreg.SetValueEx(k, "Publisher", 0, winreg.REG_SZ, PUBLISHER)
            winreg.SetValueEx(k, "DisplayIcon", 0, winreg.REG_SZ, str(exe_path))
            winreg.SetValueEx(k, "InstallLocation", 0, winreg.REG_SZ, str(install_dir))
            winreg.SetValueEx(k, "UninstallString", 0, winreg.REG_SZ, f'"{uninstaller_path}"')
            winreg.SetValueEx(k, "NoModify", 0, winreg.REG_DWORD, 1)
            winreg.SetValueEx(k, "NoRepair", 0, winreg.REG_DWORD, 1)
    except Exception:
        pass


def register_context_menu_for_exe(exe_path: Path):
    """Đăng ký menu chuột phải trỏ tới file exe đã cài đặt."""
    try:
        from vietzip.services.context_menu_service import register_context_menu
        register_context_menu(custom_exe_path=str(exe_path.resolve()))
    except Exception:
        # Fallback thủ công nếu import thất bại trong môi trường độc lập
        try:
            cmd_prefix = f'"{exe_path.resolve()}"'
            
            # Tìm file .ico trực tiếp để tránh cache PE của Windows
            ico_candidates = [
                exe_path.parent / "vietzip.ico",
                exe_path.parent / "assets" / "vietzip.ico",
                exe_path.parent / "_internal" / "assets" / "vietzip.ico",
            ]
            icon_path = f'"{exe_path.resolve()}",0'
            for ic in ico_candidates:
                if ic.exists():
                    icon_path = f'"{ic.resolve()}"'
                    break

            for k_path, val, cmd, is_dir in [
                (r"Software\Classes\*\shell\VietZIP.Compress", "Nén bằng VietZIP", f'{cmd_prefix} compress "%1"', False),
                (r"Software\Classes\Directory\shell\VietZIP.Compress", "Nén bằng VietZIP", f'{cmd_prefix} compress "%V"', True),
                (r"Software\Classes\Directory\Background\shell\VietZIP.Compress", "Nén thư mục này bằng VietZIP", f'{cmd_prefix} compress "%V"', True),
                (r"Software\Classes\SystemFileAssociations\.zip\shell\VietZIP.Extract", "Giải nén bằng VietZIP", f'{cmd_prefix} extract "%1"', False),
            ]:
                with winreg.CreateKey(winreg.HKEY_CURRENT_USER, k_path) as k:
                    winreg.SetValueEx(k, "", 0, winreg.REG_SZ, val)
                    winreg.SetValueEx(k, "Icon", 0, winreg.REG_SZ, icon_path)
                    winreg.SetValueEx(k, "MultiSelectModel", 0, winreg.REG_SZ, "Document")
                with winreg.CreateKey(winreg.HKEY_CURRENT_USER, rf"{k_path}\command") as k:
                    winreg.SetValueEx(k, "", 0, winreg.REG_SZ, cmd)

            if sys.platform == "win32":
                import ctypes
                ctypes.windll.shell32.SHChangeNotify(0x08000000, 0x0000, None, None)
        except Exception:
            pass


def create_uninstaller_script(install_dir: Path):
    """Tạo script gỡ cài đặt sạch sẽ."""
    desktop_lnk = Path.home() / "Desktop" / "VietZIP.lnk"
    start_menu_lnk = (
        Path(os.environ.get("APPDATA", ""))
        / "Microsoft"
        / "Windows"
        / "Start Menu"
        / "Programs"
        / "VietZIP"
    )

    bat_content = f"""@echo off
chcp 65001 > nul
echo Đang gỡ cài đặt VietZIP...

:: 1. Gỡ menu chuột phải
reg delete "HKCU\\Software\\Classes\\*\\shell\\VietZIP.Compress" /f >nul 2>&1
reg delete "HKCU\\Software\\Classes\\Directory\\shell\\VietZIP.Compress" /f >nul 2>&1
reg delete "HKCU\\Software\\Classes\\Directory\\Background\\shell\\VietZIP.Compress" /f >nul 2>&1
reg delete "HKCU\\Software\\Classes\\SystemFileAssociations\\.zip\\shell\\VietZIP.Extract" /f >nul 2>&1

:: 2. Gỡ thông tin Add/Remove Programs
reg delete "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\VietZIP" /f >nul 2>&1

:: 3. Xóa shortcut
del /f /q "{desktop_lnk}" >nul 2>&1
rmdir /s /q "{start_menu_lnk}" >nul 2>&1

:: 4. Tự xóa thư mục cài đặt sau khi đóng script
start /b "" cmd /c "timeout /t 1 >nul & rmdir /s /q \"{install_dir}\""

echo Gỡ cài đặt VietZIP hoàn tất!
msg * "VietZIP đã được gỡ cài đặt thành công khỏi máy tính của bạn." >nul 2>&1
"""
    uninstaller_path = install_dir / "uninstall.bat"
    try:
        with open(uninstaller_path, "w", encoding="utf-8") as fp:
            fp.write(bat_content)
    except Exception:
        pass


class SetupWizard(ctk.CTk):
    """Giao diện Wizard cài đặt chuyên nghiệp cho VietZIP."""

    def __init__(self):
        super().__init__()

        self.title(f"Cài đặt {APP_NAME} {APP_VERSION}")
        self.geometry("580x420")
        self.resizable(False, False)

        # Cấu hình AppUserModelID cho Taskbar
        if sys.platform == "win32":
            try:
                import ctypes
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("vietzip.setup.wizard.2.0")
            except Exception:
                pass

        # Set window icon cho Setup Wizard
        base_dir = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
        ico_path = base_dir / "assets" / "vietzip.ico"
        if not ico_path.exists():
            ico_path = Path(__file__).resolve().parent / "assets" / "vietzip.ico"
        if ico_path.exists():
            try:
                self.iconbitmap(str(ico_path))
            except Exception:
                pass

        png_path = base_dir / "assets" / "icon-VietZIP.png"
        if not png_path.exists():
            png_path = Path(__file__).resolve().parent / "assets" / "icon-VietZIP.png"
        if png_path.exists():
            try:
                from PIL import Image, ImageTk
                self._app_icon_photo = ImageTk.PhotoImage(Image.open(png_path))
                self.iconphoto(True, self._app_icon_photo)
            except Exception:
                pass

        # Đường dẫn cài đặt mặc định: %LOCALAPPDATA%\Programs\VietZIP
        local_app_data = os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData" / "Local"))
        default_dir = str(Path(local_app_data) / "Programs" / "VietZIP")

        self.dest_dir_var = ctk.StringVar(value=default_dir)
        self.desktop_shortcut_var = ctk.BooleanVar(value=True)
        self.start_menu_shortcut_var = ctk.BooleanVar(value=True)
        self.context_menu_var = ctk.BooleanVar(value=True)
        self.launch_after_var = ctk.BooleanVar(value=True)

        self._step = 1
        self._build_layout()
        self._show_step(1)

    def _build_layout(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Content Area
        self.content_frame = ctk.CTkFrame(self, fg_color=COLOR_CARD, corner_radius=0)
        self.content_frame.grid(row=0, column=0, sticky="nsew")

        # Bottom Button Bar
        bottom_bar = ctk.CTkFrame(self, height=52, corner_radius=0, fg_color="#F1F5F9")
        bottom_bar.grid(row=1, column=0, sticky="ew")

        self.btn_cancel = ctk.CTkButton(
            bottom_bar,
            text="Hủy",
            width=80,
            fg_color="transparent",
            border_width=1,
            text_color=COLOR_TEXT_PRIMARY,
            command=self.destroy,
        )
        self.btn_cancel.pack(side="right", padx=(6, 16), pady=12)

        self.btn_next = ctk.CTkButton(
            bottom_bar,
            text="Tiếp tục >",
            width=100,
            command=self._on_next_click,
        )
        self.btn_next.pack(side="right", padx=6, pady=12)

    def _show_step(self, step: int):
        self._step = step
        for w in self.content_frame.winfo_children():
            w.destroy()

        if step == 1:
            self._render_step1_welcome()
        elif step == 2:
            self._render_step2_options()
        elif step == 3:
            self._render_step3_installing()
        elif step == 4:
            self._render_step4_finish()

    def _render_step1_welcome(self):
        banner = ctk.CTkFrame(self.content_frame, fg_color="#0284C7", height=80, corner_radius=0)
        banner.pack(fill="x")

        # Icon VietZIP trên banner
        base_dir = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
        png_path = base_dir / "assets" / "icon-VietZIP.png"
        if not png_path.exists():
            png_path = Path(__file__).resolve().parent / "assets" / "icon-VietZIP.png"

        banner_logo = None
        if png_path.exists():
            try:
                from PIL import Image
                pil_img = Image.open(png_path)
                banner_logo = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(44, 44))
            except Exception:
                pass

        banner_left = ctk.CTkFrame(banner, fg_color="transparent")
        banner_left.pack(side="left", padx=20, pady=16)

        if banner_logo:
            ctk.CTkLabel(banner_left, text="", image=banner_logo, width=44, height=44).pack(side="left", padx=(0, 12))
        else:
            ctk.CTkLabel(banner_left, text="📦", font=("Segoe UI Emoji", 24)).pack(side="left", padx=(0, 8))

        ctk.CTkLabel(
            banner_left,
            text=f"{APP_NAME} Setup",
            font=FONT_TITLE,
            text_color="#FFFFFF",
        ).pack(side="left")

        ctk.CTkLabel(
            banner,
            text=f"Phiên bản {APP_VERSION}",
            font=FONT_REGULAR,
            text_color="#E0F2FE",
        ).pack(side="right", padx=20, pady=20)

        body = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=24, pady=20)

        ctk.CTkLabel(
            body,
            text=f"Chào mừng bạn đến với chương trình cài đặt {APP_NAME}!",
            font=FONT_SECTION,
            text_color=COLOR_TEXT_PRIMARY,
            anchor="w",
        ).pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(
            body,
            text=(
                "VietZIP là ứng dụng nén và giải nén file hiện đại, an toàn, giao diện tiếng Việt.\n\n"
                "Chương trình sẽ hướng dẫn bạn cài đặt VietZIP lên máy tính một cách dễ dàng và nhanh chóng.\n\n"
                "Nhấn 'Tiếp tục >' để bắt đầu chọn vị trí cài đặt."
            ),
            font=FONT_REGULAR,
            text_color=COLOR_TEXT_SECONDARY,
            justify="left",
            wraplength=520,
        ).pack(fill="x")

    def _render_step2_options(self):
        body = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=24, pady=20)

        ctk.CTkLabel(
            body,
            text="Chọn thư mục cài đặt:",
            font=FONT_SECTION,
            text_color=COLOR_TEXT_PRIMARY,
            anchor="w",
        ).pack(fill="x", pady=(0, 6))

        dir_row = ctk.CTkFrame(body, fg_color="transparent")
        dir_row.pack(fill="x", pady=(0, 16))

        entry = ctk.CTkEntry(dir_row, textvariable=self.dest_dir_var, text_color=COLOR_TEXT_PRIMARY)
        entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        ctk.CTkButton(
            dir_row,
            text="Duyệt...",
            width=80,
            command=self._browse_dest_dir,
        ).pack(side="right")

        ctk.CTkLabel(
            body,
            text="Tùy chọn bổ sung:",
            font=FONT_SECTION,
            text_color=COLOR_TEXT_PRIMARY,
            anchor="w",
        ).pack(fill="x", pady=(8, 6))

        ctk.CTkCheckBox(
            body,
            text="Tạo biểu tượng shortcut trên Desktop",
            variable=self.desktop_shortcut_var,
            font=FONT_REGULAR,
            text_color=COLOR_TEXT_PRIMARY,
        ).pack(anchor="w", pady=4)

        ctk.CTkCheckBox(
            body,
            text="Tạo lối tắt trong Start Menu",
            variable=self.start_menu_shortcut_var,
            font=FONT_REGULAR,
            text_color=COLOR_TEXT_PRIMARY,
        ).pack(anchor="w", pady=4)

        ctk.CTkCheckBox(
            body,
            text="Tích hợp vào Menu chuột phải (Windows Explorer)",
            variable=self.context_menu_var,
            font=FONT_REGULAR,
            text_color=COLOR_TEXT_PRIMARY,
        ).pack(anchor="w", pady=4)

    def _render_step3_installing(self):
        self.btn_next.configure(state="disabled")
        self.btn_cancel.configure(state="disabled")

        body = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=24, pady=30)

        ctk.CTkLabel(
            body,
            text="Đang cài đặt VietZIP...",
            font=FONT_SECTION,
            text_color=COLOR_TEXT_PRIMARY,
            anchor="w",
        ).pack(fill="x", pady=(0, 10))

        self.install_status_lbl = ctk.CTkLabel(
            body,
            text="Đang chuẩn bị tệp...",
            font=FONT_REGULAR,
            text_color=COLOR_TEXT_SECONDARY,
            anchor="w",
        )
        self.install_status_lbl.pack(fill="x", pady=(0, 10))

        self.install_progress = ctk.CTkProgressBar(body)
        self.install_progress.set(0)
        self.install_progress.pack(fill="x", pady=10)

        # Chạy thread cài đặt
        threading.Thread(target=self._run_install_worker, daemon=True).start()

    def _render_step4_finish(self):
        self.btn_cancel.pack_forget()
        self.btn_next.configure(state="normal", text="Hoàn tất", command=self._on_finish_click)

        body = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=24, pady=30)

        ctk.CTkLabel(
            body,
            text="🎉 Cài đặt hoàn tất!",
            font=FONT_TITLE,
            text_color="#10B981",
            anchor="w",
        ).pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(
            body,
            text=(
                f"{APP_NAME} đã được cài đặt thành công trên máy tính của bạn.\n\n"
                "Bạn có thể mở VietZIP bất cứ lúc nào từ Desktop, Start Menu, "
                "hoặc bấm chuột phải vào bất kỳ file/thư mục nào."
            ),
            font=FONT_REGULAR,
            text_color=COLOR_TEXT_SECONDARY,
            justify="left",
            wraplength=520,
        ).pack(fill="x", pady=(0, 20))

        ctk.CTkCheckBox(
            body,
            text="Khởi chạy VietZIP ngay bây giờ",
            variable=self.launch_after_var,
            font=FONT_REGULAR,
            text_color=COLOR_TEXT_PRIMARY,
        ).pack(anchor="w")

    def _browse_dest_dir(self):
        d = filedialog.askdirectory(title="Chọn thư mục cài đặt")
        if d:
            self.dest_dir_var.set(str(Path(d) / "VietZIP"))

    def _on_next_click(self):
        if self._step == 1:
            self._show_step(2)
        elif self._step == 2:
            self._show_step(3)

    def _on_finish_click(self):
        dest_dir = Path(self.dest_dir_var.get())
        exe_file = dest_dir / "VietZIP.exe"
        if self.launch_after_var.get() and exe_file.exists():
            subprocess.Popen([str(exe_file)], cwd=str(dest_dir))
        self.destroy()

    def _run_install_worker(self):
        dest_dir = Path(self.dest_dir_var.get()).resolve()
        dest_dir.mkdir(parents=True, exist_ok=True)

        # 1. Tìm payload (payload.zip đính kèm trong thư mục chạy hoặc bên cạnh)
        base_dir = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
        payload_zip = base_dir / "payload.zip"

        if not payload_zip.exists():
            # Fallback trong thư mục phát triển: nén từ dist/VietZIP
            dist_source = Path(__file__).resolve().parent / "dist" / "VietZIP"
            if dist_source.exists():
                self.install_status_lbl.configure(text="Đang sao chép tệp chương trình...")
                shutil.copytree(dist_source, dest_dir, dirs_exist_ok=True)
            else:
                messagebox.showerror("Lỗi", "Không tìm thấy dữ liệu cài đặt (payload.zip)!")
                self.destroy()
                return
        else:
            self.install_status_lbl.configure(text="Đang giải nén tệp chương trình...")
            with zipfile.ZipFile(payload_zip, "r") as zf:
                infolist = zf.infolist()
                total = len(infolist)
                for idx, item in enumerate(infolist, start=1):
                    zf.extract(item, dest_dir)
                    self.install_progress.set(idx / total)
                    self.install_status_lbl.configure(text=f"Đang cài đặt: {item.filename}")

        exe_path = dest_dir / "VietZIP.exe"

        # Đảm bảo có file vietzip.ico ở thư mục cài đặt để shortcut trỏ trực tiếp
        ico_file = dest_dir / "vietzip.ico"
        internal_ico = dest_dir / "_internal" / "assets" / "vietzip.ico"
        assets_ico = dest_dir / "assets" / "vietzip.ico"
        if not ico_file.exists():
            if internal_ico.exists():
                try:
                    shutil.copy2(internal_ico, ico_file)
                except Exception:
                    pass
            elif assets_ico.exists():
                try:
                    shutil.copy2(assets_ico, ico_file)
                except Exception:
                    pass

        shortcut_icon = ico_file if ico_file.exists() else exe_path

        # 2. Tạo shortcuts
        self.install_status_lbl.configure(text="Đang tạo các biểu tượng lối tắt...")
        if self.desktop_shortcut_var.get():
            desktop_lnk = Path.home() / "Desktop" / "VietZIP.lnk"
            create_windows_shortcut(desktop_lnk, exe_path, shortcut_icon, dest_dir)
            onedrive_desk = Path.home() / "OneDrive" / "Desktop" / "VietZIP.lnk"
            if onedrive_desk.parent.exists():
                create_windows_shortcut(onedrive_desk, exe_path, shortcut_icon, dest_dir)

        if self.start_menu_shortcut_var.get():
            start_dir = (
                Path(os.environ.get("APPDATA", ""))
                / "Microsoft"
                / "Windows"
                / "Start Menu"
                / "Programs"
                / "VietZIP"
            )
            start_dir.mkdir(parents=True, exist_ok=True)
            start_lnk = start_dir / "VietZIP.lnk"
            create_windows_shortcut(start_lnk, exe_path, shortcut_icon, dest_dir)

        # 3. Tạo uninstaller script và đăng ký Windows Apps
        self.install_status_lbl.configure(text="Đang tạo trình gỡ cài đặt...")
        create_uninstaller_script(dest_dir)
        register_uninstall_info(dest_dir)

        # 4. Đăng ký menu chuột phải nếu được chọn
        if self.context_menu_var.get():
            self.install_status_lbl.configure(text="Đang tích hợp menu chuột phải...")
            register_context_menu_for_exe(exe_path)

        # 5. Thông báo Windows Shell làm mới icon cache trên Desktop & Explorer
        if sys.platform == "win32":
            try:
                import ctypes
                ctypes.windll.shell32.SHChangeNotify(0x08000000, 0x0000, None, None)
            except Exception:
                pass

        # Chuyển sang màn hình hoàn tất
        self.after(400, lambda: self._show_step(4))


def main():
    app = SetupWizard()
    app.mainloop()


if __name__ == "__main__":
    main()
