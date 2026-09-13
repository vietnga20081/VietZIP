"""Main application window with CustomTkinter and optional TkinterDnD integration."""

from __future__ import annotations

import os
import queue
import sys
import threading
import time
from pathlib import Path
from tkinter import messagebox
from typing import Optional

import customtkinter as ctk

try:
    from tkinterdnd2 import TkinterDnD, DND_FILES
    HAS_DND = True
except Exception:
    HAS_DND = False

from vietzip.core.compressor import compress_archive
from vietzip.core.extractor import extract_archive
from vietzip.core.models import (
    OperationResult,
    OperationType,
    OverwritePolicy,
    ProgressInfo,
)
from vietzip.services.history_service import history_service
from vietzip.services.ipc_service import normalize_input_path
from vietzip.services.settings_service import settings_service
from vietzip.ui.about_view import AboutWindow
from vietzip.ui.compress_view import CompressView
from vietzip.ui.extract_view import ExtractView
from vietzip.ui.history_view import HistoryWindow
from vietzip.ui.settings_view import SettingsWindow
from vietzip.ui.theme import (
    APP_NAME,
    APP_SUBTITLE,
    COLOR_BG,
    COLOR_BORDER,
    COLOR_CARD,
    COLOR_DANGER,
    COLOR_DANGER_HOVER,
    COLOR_PRIMARY,
    COLOR_BTN_OUTLINE_TEXT,
    COLOR_SEGMENT_TEXT,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    BTN_SECONDARY_STYLE,
    FONT_MONO,
    FONT_REGULAR,
    FONT_SECTION,
    FONT_SMALL,
    FONT_SUBTITLE,
    FONT_TITLE,
    MASCOT_CANCELLED,
    MASCOT_ERROR,
    MASCOT_IDLE,
    MASCOT_SUCCESS,
    MASCOT_WORKING,
    init_theme,
)
from vietzip.ui.widgets import OverwriteDialog, ToastNotification, bring_to_front
from vietzip.utils.file_utils import get_asset_path, open_in_explorer
from vietzip.utils.format_utils import format_eta, format_speed, human_size
from vietzip.utils.logging_utils import logger


# Lớp cơ sở tích hợp DnD an toàn
if HAS_DND:
    class BaseWindow(ctk.CTk, TkinterDnD.DnDWrapper):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            try:
                self.TkdndVersion = TkinterDnD._require(self)
            except Exception as e:
                logger.warning("Không thể kích hoạt TkinterDnD: %s", e)
else:
    class BaseWindow(ctk.CTk):
        pass


class MainWindow(BaseWindow):
    """Cửa sổ chính của ứng dụng VietZIP."""

    def __init__(
        self,
        initial_action: Optional[str] = None,
        initial_paths: Optional[list[str]] = None,
    ):
        super().__init__()

        # Áp dụng theme đã lưu
        saved_theme = settings_service.get("theme", "System")
        init_theme(saved_theme)

        self.title(f"{APP_NAME} — {APP_SUBTITLE}")
        self.geometry("920x680")
        self.minsize(800, 600)

        # Cấu hình AppUserModelID cho Windows Taskbar để hiển thị đúng icon ứng dụng
        if sys.platform == "win32":
            try:
                import ctypes
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("vietzip.application.2.0")
            except Exception:
                pass

        # Set window icon cho Title Bar và Taskbar
        ico_path = get_asset_path("vietzip.ico")
        if ico_path.exists():
            try:
                self.iconbitmap(str(ico_path))
            except Exception:
                pass

        png_path = get_asset_path("icon-VietZIP.png")
        if png_path.exists():
            try:
                from PIL import Image, ImageTk
                pil_icon = Image.open(png_path)
                self._app_icon_photo = ImageTk.PhotoImage(pil_icon)
                self.iconphoto(True, self._app_icon_photo)
            except Exception:
                pass

        # Trạng thái tác vụ
        self.msg_queue: queue.Queue = queue.Queue()
        self.cancel_event = threading.Event()
        self.current_worker: Optional[threading.Thread] = None
        self.is_working = False
        self._mascot_frame = 0

        # Cửa sổ phụ
        self._history_win: Optional[HistoryWindow] = None
        self._settings_win: Optional[SettingsWindow] = None
        self._about_win: Optional[AboutWindow] = None

        self._build_layout()
        self._setup_drag_and_drop()
        self._setup_shortcuts()

        # Xử lý tham số dòng lệnh ban đầu (từ Menu chuột phải hoặc mở file)
        self._handle_initial_args(initial_action, initial_paths)

        # Bắt đầu vòng lặp đọc hàng đợi
        self.after(80, self._poll_queue)

    def _handle_initial_args(
        self, initial_action: Optional[str], initial_paths: Optional[list[str]]
    ):
        if not initial_paths:
            return

        valid_paths = [normalize_input_path(p) for p in initial_paths]
        valid_paths = [p for p in valid_paths if p and os.path.exists(p)]
        if not valid_paths:
            return

        # Nếu là file zip hoặc action extract
        if initial_action == "extract" or (
            initial_action != "compress"
            and len(valid_paths) == 1
            and valid_paths[0].lower().endswith(".zip")
        ):
            self.tabview.set("📂  Giải nén")
            self.extract_view.load_zip(valid_paths[0])
        else:
            self.tabview.set("🗜️  Nén file")
            self.compress_view.add_paths(valid_paths)

    def on_ipc_received(self, action: str, paths: list[str]):
        """Nhận đường dẫn từ tiến trình VietZIP khác (khi người dùng chọn nhiều file ở Explorer)."""
        def _process():
            valid_paths = [normalize_input_path(p) for p in paths]
            valid_paths = [p for p in valid_paths if p and os.path.exists(p)]
            if not valid_paths:
                return

            try:
                self.deiconify()
                self.lift()
                self.focus_force()
                self.attributes("-topmost", True)
                self.after(250, lambda: self.attributes("-topmost", False))
            except Exception:
                pass

            if action == "extract" or (
                action != "compress"
                and len(valid_paths) == 1
                and valid_paths[0].lower().endswith(".zip")
            ):
                self.tabview.set("📂  Giải nén")
                self.extract_view.load_zip(valid_paths[0])
            else:
                self.tabview.set("🗜️  Nén file")
                self.compress_view.add_paths(valid_paths)

        self.after(0, _process)

    def _build_layout(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # 1. Header
        header = ctk.CTkFrame(
            self,
            corner_radius=0,
            fg_color=COLOR_CARD,
            border_width=1,
            border_color=COLOR_BORDER,
        )
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(1, weight=1)

        # Logo ứng dụng trên Header
        self.logo_img = None
        logo_path = get_asset_path("icon-VietZIP.png")
        if logo_path.exists():
            try:
                from PIL import Image
                pil_logo = Image.open(logo_path)
                self.logo_img = ctk.CTkImage(light_image=pil_logo, dark_image=pil_logo, size=(48, 48))
            except Exception as e:
                logger.warning("Không thể tải logo header: %s", e)

        if self.logo_img:
            self.logo_lbl = ctk.CTkLabel(header, text="", image=self.logo_img, width=48, height=48)
        else:
            self.logo_lbl = ctk.CTkLabel(header, text="🗜️", font=("Segoe UI Emoji", 32), width=48)
        self.logo_lbl.grid(row=0, column=0, padx=(18, 12), pady=12)
        self.mascot_lbl = self.logo_lbl

        # Title + Subtitle
        title_box = ctk.CTkFrame(header, fg_color="transparent")
        title_box.grid(row=0, column=1, sticky="w", pady=12)

        ctk.CTkLabel(
            title_box,
            text=APP_NAME,
            font=FONT_TITLE,
            text_color=COLOR_TEXT_PRIMARY,
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_box,
            text=APP_SUBTITLE,
            font=FONT_SUBTITLE,
            text_color=COLOR_TEXT_SECONDARY,
        ).pack(anchor="w")

        # Right Header Actions
        right_box = ctk.CTkFrame(header, fg_color="transparent")
        right_box.grid(row=0, column=2, padx=16, pady=12, sticky="e")

        # Theme Selector
        self.theme_btn = ctk.CTkSegmentedButton(
            right_box,
            values=["☀️ Sáng", "🌙 Tối", "🖥️ Hệ thống"],
            text_color=COLOR_SEGMENT_TEXT,
            unselected_color=("#E2E8F0", "gray29"),
            unselected_hover_color=("#CBD5E1", "gray41"),
            command=self._on_theme_changed,
        )
        theme_map = {"Light": "☀️ Sáng", "Dark": "🌙 Tối", "System": "🖥️ Hệ thống"}
        cur_theme = settings_service.get("theme", "System")
        self.theme_btn.set(theme_map.get(cur_theme, "🖥️ Hệ thống"))
        self.theme_btn.pack(side="left", padx=(0, 10))

        # History Button
        ctk.CTkButton(
            right_box,
            text="🕘 Lịch sử",
            width=90,
            height=30,
            **BTN_SECONDARY_STYLE,
            command=self._open_history,
        ).pack(side="left", padx=(0, 6))

        # Settings Button
        ctk.CTkButton(
            right_box,
            text="⚙️",
            width=36,
            height=30,
            **BTN_SECONDARY_STYLE,
            command=self._open_settings,
        ).pack(side="left", padx=(0, 6))

        # About Team & Donate Button
        ctk.CTkButton(
            right_box,
            text="ℹ️ Giới thiệu",
            width=95,
            height=30,
            **BTN_SECONDARY_STYLE,
            command=self._open_about,
        ).pack(side="left")

        # 2. Main Tabview
        self.tabview = ctk.CTkTabview(
            self,
            corner_radius=14,
            text_color=COLOR_SEGMENT_TEXT,
            segmented_button_unselected_color=("#E2E8F0", "gray29"),
            segmented_button_unselected_hover_color=("#CBD5E1", "gray41"),
        )
        self.tabview.grid(row=1, column=0, sticky="nsew", padx=16, pady=(10, 6))

        tab_comp = self.tabview.add("🗜️  Nén file")
        tab_ext = self.tabview.add("📂  Giải nén")

        tab_comp.grid_columnconfigure(0, weight=1)
        tab_comp.grid_rowconfigure(0, weight=1)
        tab_ext.grid_columnconfigure(0, weight=1)
        tab_ext.grid_rowconfigure(0, weight=1)

        self.compress_view = CompressView(
            tab_comp,
            on_start_compress=self._start_compression_task,
        )
        self.compress_view.grid(row=0, column=0, sticky="nsew")

        self.extract_view = ExtractView(
            tab_ext,
            on_start_extract=self._start_extraction_task,
        )
        self.extract_view.grid(row=0, column=0, sticky="nsew")

        # 3. Status & Progress Bar at bottom
        self.status_bar = ctk.CTkFrame(
            self,
            corner_radius=12,
            border_width=1,
            border_color=COLOR_BORDER,
            fg_color=COLOR_CARD,
        )
        self.status_bar.grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 14))
        self.status_bar.grid_columnconfigure(0, weight=1)

        # Row 0: Progress Bar + Cancel Button
        prog_row = ctk.CTkFrame(self.status_bar, fg_color="transparent")
        prog_row.grid(row=0, column=0, sticky="ew", padx=14, pady=(10, 4))
        prog_row.grid_columnconfigure(0, weight=1)

        self.progress_bar = ctk.CTkProgressBar(prog_row)
        self.progress_bar.set(0)
        self.progress_bar.grid(row=0, column=0, sticky="ew", padx=(0, 10))

        self.cancel_btn = ctk.CTkButton(
            prog_row,
            text="⏹ Hủy",
            width=80,
            height=26,
            fg_color=COLOR_DANGER,
            hover_color=COLOR_DANGER_HOVER,
            command=self._cancel_current_task,
        )
        self.cancel_btn.grid(row=0, column=1)
        self.cancel_btn.configure(state="disabled")

        # Row 1: Detailed Status & Metrics
        metrics_row = ctk.CTkFrame(self.status_bar, fg_color="transparent")
        metrics_row.grid(row=1, column=0, sticky="ew", padx=14, pady=(0, 10))
        metrics_row.grid_columnconfigure(0, weight=1)

        self.status_lbl = ctk.CTkLabel(
            metrics_row,
            text="Sẵn sàng! Hãy chọn file hoặc thư mục để bắt đầu 😺",
            font=FONT_REGULAR,
            anchor="w",
            text_color=COLOR_TEXT_PRIMARY,
        )
        self.status_lbl.grid(row=0, column=0, sticky="w")

        self.metrics_lbl = ctk.CTkLabel(
            metrics_row,
            text="",
            font=FONT_MONO,
            anchor="e",
            text_color=COLOR_TEXT_SECONDARY,
        )
        self.metrics_lbl.grid(row=0, column=1, sticky="e")

    def _setup_drag_and_drop(self):
        """Đăng ký sự kiện Drag & Drop nếu thư viện hỗ trợ."""
        if not HAS_DND or not hasattr(self, "drop_target_register"):
            return

        try:
            self.drop_target_register(DND_FILES)
            self.dnd_bind("<<Drop>>", self._on_files_dropped)
            logger.info("Đã đăng ký sự kiện kéo thả file (Drag & Drop) thành công.")
        except Exception as exc:
            logger.warning("Không thể đăng ký DnD: %s", exc)

    def _on_files_dropped(self, event):
        """Xử lý khi người dùng kéo thả file từ Explorer vào cửa sổ."""
        if not event.data:
            return

        raw = event.data
        # Trích xuất danh sách file từ chuỗi DnD (hỗ trợ Windows path có khoảng trắng dạng {path})
        paths = []
        if "{" in raw:
            import re
            matches = re.findall(r"\{(.*?)\}", raw)
            paths.extend(matches)
            remaining = re.sub(r"\{(.*?)\}", "", raw).split()
            paths.extend(remaining)
        else:
            paths = raw.split()

        clean_paths = [os.path.normpath(p.strip()) for p in paths if p.strip()]

        current_tab = self.tabview.get()
        if "Giải nén" in current_tab:
            # Nếu đang ở tab Giải nén và có file .zip, nạp vào
            zip_files = [p for p in clean_paths if p.lower().endswith(".zip")]
            if zip_files:
                self.extract_view.load_zip(zip_files[0])
            else:
                self.compress_view.add_paths(clean_paths)
                self.tabview.set("🗜️  Nén file")
        else:
            # Nếu kéo một file ZIP vào tab Nén, có thể là muốn giải nén
            if len(clean_paths) == 1 and clean_paths[0].lower().endswith(".zip"):
                self.extract_view.load_zip(clean_paths[0])
                self.tabview.set("📂  Giải nén")
            else:
                self.compress_view.add_paths(clean_paths)

    def _setup_shortcuts(self):
        """Thiết lập phím tắt."""
        self.bind("<Control-o>", lambda e: self.compress_view._add_files())
        self.bind("<Control-O>", lambda e: self.compress_view._add_folder())
        self.bind("<Escape>", lambda e: self._cancel_current_task())
        self.bind("<Control-comma>", lambda e: self._open_settings())

    def _on_theme_changed(self, choice: str):
        mapping = {"☀️ Sáng": "Light", "🌙 Tối": "Dark", "🖥️ Hệ thống": "System"}
        val = mapping.get(choice, "System")
        ctk.set_appearance_mode(val)
        settings_service.set("theme", val)

    def _set_mascot(self, pool: list[str], frame: int = 0):
        # Nếu đã có logo hình ảnh chính thức ở header thì luôn hiển thị logo đó
        if getattr(self, "logo_img", None) is not None:
            return
        if not settings_service.get("show_mascot", True):
            self.mascot_lbl.configure(text="")
            return
        self.mascot_lbl.configure(text=pool[frame % len(pool)])

    def _open_history(self):
        if self._history_win is None or not self._history_win.winfo_exists():
            self._history_win = HistoryWindow(self)
        else:
            bring_to_front(self._history_win, self)

    def _open_settings(self):
        if self._settings_win is None or not self._settings_win.winfo_exists():
            self._settings_win = SettingsWindow(
                self,
                on_theme_change=lambda t: self._on_theme_changed(
                    {"Light": "☀️ Sáng", "Dark": "🌙 Tối", "System": "🖥️ Hệ thống"}.get(t, "🖥️ Hệ thống")
                ),
            )
        else:
            bring_to_front(self._settings_win, self)

    def _open_about(self):
        if self._about_win is None or not self._about_win.winfo_exists():
            self._about_win = AboutWindow(self)
        else:
            bring_to_front(self._about_win, self)

    # ------------------------------------------------ Tác vụ Nén & Giải nén --
    def _start_compression_task(
        self,
        sources: list[str],
        output_path: str,
        level: int,
        password: Optional[str],
        verify: bool,
    ):
        if self.is_working:
            return

        self._set_busy_state(True, "Đang nén dữ liệu...")
        self.cancel_event.clear()

        def worker():
            def on_progress(p_info: ProgressInfo):
                self.msg_queue.put(("progress", p_info))

            res = compress_archive(
                sources=sources,
                output_path=output_path,
                level=level,
                password=password,
                verify=verify,
                cancel_event=self.cancel_event,
                progress_callback=on_progress,
            )
            self.msg_queue.put(("result", res, sources))

        self.current_worker = threading.Thread(target=worker, daemon=True)
        self.current_worker.start()

    def _start_extraction_task(
        self,
        zip_path: str,
        dest_dir: str,
        password: Optional[str],
    ):
        if self.is_working:
            return

        self._set_busy_state(True, "Đang giải nén dữ liệu...")
        self.cancel_event.clear()

        # Overwrite policy từ settings
        ow_val = settings_service.get("overwrite_policy", "auto_rename")
        default_policy = OverwritePolicy(ow_val)

        def worker():
            def on_progress(p_info: ProgressInfo):
                self.msg_queue.put(("progress", p_info))

            res = extract_archive(
                zip_path=zip_path,
                dest_dir=dest_dir,
                password=password,
                overwrite_policy=default_policy,
                cancel_event=self.cancel_event,
                progress_callback=on_progress,
            )
            self.msg_queue.put(("result", res, [zip_path]))

        self.current_worker = threading.Thread(target=worker, daemon=True)
        self.current_worker.start()

    def _cancel_current_task(self):
        if not self.is_working:
            return
        self.status_lbl.configure(text="Đang hủy tác vụ...")
        self.cancel_event.set()

    def _set_busy_state(self, is_busy: bool, status_text: str = ""):
        self.is_working = is_busy
        self.compress_view.set_busy(is_busy)
        self.extract_view.set_busy(is_busy)

        if is_busy:
            self.cancel_btn.configure(state="normal")
            self.progress_bar.set(0)
            self.status_lbl.configure(text=status_text)
            self.metrics_lbl.configure(text="")
            self._set_mascot(MASCOT_WORKING)
        else:
            self.cancel_btn.configure(state="disabled")

    # ----------------------------------------------------------- Hàng đợi --
    def _poll_queue(self):
        try:
            while True:
                msg = self.msg_queue.get_nowait()
                kind = msg[0]

                if kind == "progress":
                    p_info: ProgressInfo = msg[1]
                    self.progress_bar.set(p_info.percent)
                    self.status_lbl.configure(
                        text=f"{p_info.operation}: {Path(p_info.current_file).name or p_info.current_file}"
                    )

                    pct_str = f"{int(p_info.percent * 100)}%"
                    proc_str = f"{human_size(p_info.processed_bytes)} / {human_size(p_info.total_bytes)}"
                    spd_str = format_speed(p_info.speed_bps)
                    eta_str = f"còn {format_eta(p_info.eta_seconds)}"

                    self.metrics_lbl.configure(
                        text=f"{pct_str} • {proc_str} • {spd_str} • {eta_str}"
                    )

                    self._mascot_frame += 1
                    self._set_mascot(MASCOT_WORKING, self._mascot_frame // 2)

                elif kind == "result":
                    res: OperationResult = msg[1]
                    sources = msg[2]
                    self._handle_operation_result(res, sources)

        except queue.Empty:
            pass
        finally:
            self.after(80, self._poll_queue)

    def _handle_operation_result(self, res: OperationResult, sources: list[str]):
        self._set_busy_state(False)

        if res.cancelled:
            self.status_lbl.configure(text="Đã hủy thao tác.")
            self.metrics_lbl.configure(text="")
            self.progress_bar.set(0)
            self._set_mascot(MASCOT_CANCELLED)

            if settings_service.get("history_enabled", True):
                history_service.add_record(
                    operation=res.operation,
                    input_summary=", ".join(Path(s).name for s in sources[:3]),
                    output_path=res.output_path or "",
                    file_count=res.file_count,
                    original_size=res.original_size,
                    final_size=res.compressed_size,
                    elapsed_seconds=res.elapsed_seconds,
                    status="cancelled",
                )
            return

        if not res.success:
            err_msg = res.error or "Có lỗi không xác định xảy ra."
            self.status_lbl.configure(text=f"⚠️ Lỗi: {err_msg}")
            self.metrics_lbl.configure(text="")
            self._set_mascot(MASCOT_ERROR)

            if settings_service.get("history_enabled", True):
                history_service.add_record(
                    operation=res.operation,
                    input_summary=", ".join(Path(s).name for s in sources[:3]),
                    output_path=res.output_path or "",
                    file_count=res.file_count,
                    original_size=res.original_size,
                    final_size=res.compressed_size,
                    elapsed_seconds=res.elapsed_seconds,
                    status="error",
                    error_message=err_msg,
                )

            messagebox.showerror(
                "Lỗi tác vụ — VietZIP",
                f"Tác vụ không thành công:\n\n{err_msg}\n\nChi tiết: {res.error_details}",
                parent=self,
            )
            return

        # Thành công
        self.progress_bar.set(1.0)
        self._set_mascot(MASCOT_SUCCESS)

        if res.operation == "compress":
            ratio = 0.0
            if res.original_size > 0:
                ratio = max(0.0, (1 - res.compressed_size / res.original_size) * 100)

            msg_text = (
                f"Đã nén {res.file_count} mục: {human_size(res.original_size)} ➜ "
                f"{human_size(res.compressed_size)} (giảm {ratio:.1f}%) trong {res.elapsed_seconds:.1f}s"
            )
            self.status_lbl.configure(text=f"✓ Nén thành công: {Path(res.output_path).name}")
            self.metrics_lbl.configure(text=f"{human_size(res.compressed_size)} • {res.elapsed_seconds:.1f}s")

            # Toast notification
            ToastNotification(
                self,
                title="✓ Nén thành công!",
                message=f"{Path(res.output_path).name}\n{msg_text}",
                target_path=res.output_path,
            ).place(relx=1.0, rely=1.0, x=-24, y=-80, anchor="se")

        else:
            msg_text = f"Đã giải nén {res.file_count} mục vào thư mục đích ({res.elapsed_seconds:.1f}s)."
            self.status_lbl.configure(text=f"✓ Giải nén thành công vào: {Path(res.output_path).name}")
            self.metrics_lbl.configure(text=f"{res.file_count} mục • {res.elapsed_seconds:.1f}s")

            ToastNotification(
                self,
                title="✓ Giải nén thành công!",
                message=f"{Path(res.output_path).name}\n{msg_text}",
                target_path=res.output_path,
            ).place(relx=1.0, rely=1.0, x=-24, y=-80, anchor="se")

        # Lưu lịch sử
        if settings_service.get("history_enabled", True):
            history_service.add_record(
                operation=res.operation,
                input_summary=", ".join(Path(s).name for s in sources[:3]),
                output_path=res.output_path or "",
                file_count=res.file_count,
                original_size=res.original_size,
                final_size=res.compressed_size,
                elapsed_seconds=res.elapsed_seconds,
                status="success",
            )

        # Tự động mở thư mục nếu được bật trong cài đặt
        if settings_service.get("open_folder_after_operation", True) and res.output_path:
            open_in_explorer(res.output_path)
