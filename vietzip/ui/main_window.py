"""Cửa sổ chính: điều phối header, chế độ Nén/Giải nén, tiến trình, kết quả, DnD, phím tắt, IPC.

Giữ nguyên kiến trúc worker thread + queue; core được gọi y như trước.
"""

from __future__ import annotations

import os
import queue
import sys
import threading
import time
import tkinter as tk
from pathlib import Path
from tkinter import messagebox
from typing import Callable, Optional

import customtkinter as ctk

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    HAS_DND = True
except Exception:  # noqa: BLE001
    HAS_DND = False

from vietzip import __version__
from vietzip.core.compressor import compress_archive
from vietzip.core.extractor import extract_archive
from vietzip.core.models import OperationResult, OverwritePolicy, ProgressInfo
from vietzip.services.history_service import history_service
from vietzip.services.ipc_service import normalize_input_path
from vietzip.services.recent_service import recent_service
from vietzip.services.settings_service import settings_service
from vietzip.ui.about_view import AboutWindow
from vietzip.ui.components import (
    AppHeader,
    ModeSwitch,
    ProgressPanel,
    ResultPanel,
    ToastManager,
)
from vietzip.ui.compress_view import CompressView
from vietzip.ui.extract_view import ExtractView, is_zip
from vietzip.ui.history_view import HistoryWindow
from vietzip.ui.settings_view import SettingsWindow
from vietzip.ui.theme import (
    APP_NAME,
    APP_TAGLINE,
    COLOR_BG,
    COLOR_BORDER,
    COLOR_SURFACE,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_SECONDARY,
    FONT_SMALL,
    SP8,
    SP12,
    SP24,
    init_theme,
)
from vietzip.ui.widgets import (
    apply_window_icon,
    bring_to_front,
    get_logo_image,
    get_window_icon_pil,
)
from vietzip.utils.error_utils import friendly_error
from vietzip.utils.file_utils import open_file, open_in_explorer
from vietzip.utils.format_utils import format_duration, human_size
from vietzip.utils.logging_utils import logger
from vietzip.utils.path_utils import parse_dropped_paths

CANCEL_CONFIRM_AFTER_S = 15  # hỏi xác nhận hủy nếu tác vụ đã chạy lâu
POLL_MS = 50

if HAS_DND:
    class BaseWindow(ctk.CTk, TkinterDnD.DnDWrapper):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            try:
                self.TkdndVersion = TkinterDnD._require(self)
            except Exception as e:  # noqa: BLE001
                logger.warning("Không thể kích hoạt TkinterDnD: %s", e)
else:
    class BaseWindow(ctk.CTk):
        pass


class MainWindow(BaseWindow):
    """Cửa sổ chính VietZIP."""

    def __init__(self, initial_action: Optional[str] = None, initial_paths: Optional[list[str]] = None):
        super().__init__()
        init_theme(settings_service.get("theme", "System"))
        self.title(f"{APP_NAME} — {APP_TAGLINE}")
        self.geometry("920x680")
        self.minsize(800, 600)
        self.configure(fg_color=COLOR_BG)
        self._setup_icon()

        # Trạng thái tác vụ
        self.msg_queue: queue.Queue = queue.Queue()
        self.cancel_event = threading.Event()
        self.current_worker: Optional[threading.Thread] = None
        self.is_working = False
        self._task_start = 0.0
        self._task_op = "compress"
        self._task_verify = False
        self._retry: Optional[Callable[[], None]] = None  # giữ tạm để 'Thử lại'; xóa khi đóng
        self._stage = "compress"  # compress | extract | progress | result

        self._history_win: Optional[HistoryWindow] = None
        self._settings_win: Optional[SettingsWindow] = None
        self._about_win: Optional[AboutWindow] = None

        self._build_layout()
        self.toasts = ToastManager(self)
        self._setup_drag_and_drop()
        self._setup_shortcuts()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self._route_paths(initial_action, initial_paths or [], from_drop=False)
        self.after(POLL_MS, self._poll_queue)

    # ------------------------------------------------------------------ Khởi tạo
    def _setup_icon(self):
        if sys.platform == "win32":
            try:
                import ctypes
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("vietzip.application.2.0")
            except Exception:  # noqa: BLE001
                pass
        apply_window_icon(self)
        pil = get_window_icon_pil()
        if pil is not None:
            try:
                from PIL import ImageTk
                self._app_icon_photo = ImageTk.PhotoImage(pil)
                self.iconphoto(True, self._app_icon_photo)
            except Exception:  # noqa: BLE001
                pass

    def _build_layout(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self.header = AppHeader(
            self,
            logo_image=get_logo_image(40),
            current_theme=settings_service.get("theme", "System"),
            on_theme=self.apply_theme,
            on_history=self._open_history,
            on_settings=self._open_settings,
            on_about=self._open_about,
            get_recent=recent_service.get_all,
            on_open_recent=lambda p: self._route_paths("extract", [p], from_drop=False),
            on_clear_recent=self._clear_recent,
        )
        self.header.grid(row=0, column=0, sticky="ew")

        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.grid(row=1, column=0, pady=(SP12, 0))
        self.mode_switch = ModeSwitch(bar, on_change=self._on_mode_changed)
        self.mode_switch.pack()

        self.stage_host = ctk.CTkFrame(self, fg_color="transparent")
        self.stage_host.grid(row=2, column=0, sticky="nsew", padx=SP24, pady=SP12)
        self.stage_host.grid_columnconfigure(0, weight=1)
        self.stage_host.grid_rowconfigure(0, weight=1)

        self.compress_view = CompressView(self.stage_host, on_start=self._start_compression, notify=self.notify)
        self.extract_view = ExtractView(self.stage_host, on_start=self._start_extraction, notify=self.notify)
        self.progress_panel = ProgressPanel(self.stage_host, on_cancel=self._request_cancel)
        self.result_panel = ResultPanel(self.stage_host)
        self._stages = {
            "compress": self.compress_view,
            "extract": self.extract_view,
            "progress": self.progress_panel,
            "result": self.result_panel,
        }
        self._show("compress")

        status = ctk.CTkFrame(self, corner_radius=0, fg_color=COLOR_SURFACE)
        status.grid(row=3, column=0, sticky="ew")
        ctk.CTkFrame(status, height=1, fg_color=COLOR_BORDER, corner_radius=0).pack(fill="x")
        inner = ctk.CTkFrame(status, fg_color="transparent")
        inner.pack(fill="x", padx=SP24, pady=(SP8, SP8))
        self.status_lbl = ctk.CTkLabel(inner, text="Sẵn sàng", font=FONT_SMALL, text_color=COLOR_TEXT_SECONDARY)
        self.status_lbl.pack(side="left")
        ctk.CTkLabel(
            inner, text=f"Ctrl+O chọn file  ·  Ctrl+H lịch sử  ·  v{__version__}",
            font=FONT_SMALL, text_color=COLOR_TEXT_MUTED,
        ).pack(side="right")

    # ------------------------------------------------------------------ Điều hướng
    def _show(self, stage: str):
        self._stage = stage
        for name, frame in self._stages.items():
            if name == stage:
                frame.grid(row=0, column=0, sticky="nsew")
            else:
                frame.grid_remove()

    def _on_mode_changed(self, mode: str):
        if not self.is_working and self._stage in ("compress", "extract"):
            self._show(mode)

    def _go_mode(self, mode: str):
        """Chuyển về màn hình nhập liệu của chế độ `mode` (nếu không đang chạy)."""
        if self.is_working:
            return
        self.mode_switch.select(mode, notify=False)
        self._show(mode)
        self.set_status("Sẵn sàng")

    def _current_view(self):
        return self.extract_view if self.mode_switch.mode == "extract" else self.compress_view

    def set_status(self, text: str):
        self.status_lbl.configure(text=text)

    def notify(self, kind: str, title: str, message: str = ""):
        self.toasts.show(kind, title, message)

    def apply_theme(self, mode: str):
        ctk.set_appearance_mode(mode)
        settings_service.set("theme", mode)
        self.header.set_theme(mode)

    def _clear_recent(self):
        recent_service.clear()
        self.notify("info", "Đã xóa danh sách gần đây")

    # ------------------------------------------------------------------ Định tuyến đường dẫn (menu chuột phải / IPC / kéo thả)
    def _route_paths(self, action: Optional[str], paths: list[str], from_drop: bool) -> bool:
        valid = [normalize_input_path(p) for p in paths]
        valid = [p for p in valid if p and os.path.exists(p)]
        if not valid:
            return False

        if self.is_working:
            # Đang bận: vẫn ghi nhận vào danh sách nén để không mất file, báo cho người dùng biết.
            if not (action == "extract" or (len(valid) == 1 and is_zip(valid[0]) and action != "compress")):
                n = self.compress_view.add_paths(valid)
                self.notify("info", f"Đã thêm {n} mục vào danh sách nén", "Sẽ hiển thị sau khi tác vụ hiện tại kết thúc.")
            else:
                self.notify("warning", "Đang bận", "Hãy đợi tác vụ hiện tại hoàn tất rồi mở file ZIP.")
            return True

        if self._stage == "result":
            self._show(self.mode_switch.mode)

        compress_empty = not self.compress_view.items
        wants_extract = action == "extract" or (
            action != "compress"
            and len(valid) == 1
            and is_zip(valid[0])
            and (compress_empty or not from_drop)
        )
        # Đang ở chế độ Giải nén và có ít nhất một ZIP: mở ZIP đầu tiên
        if not wants_extract and action is None and self.mode_switch.mode == "extract":
            zips = [p for p in valid if is_zip(p)]
            if zips and len(zips) == len(valid):
                wants_extract = True
                valid = zips

        if wants_extract:
            zips = [p for p in valid if is_zip(p)] or valid
            self._go_mode("extract")
            self.extract_view.load_zip(zips[0])
            if len(zips) > 1:
                self.notify("info", "Chỉ mở được 1 file ZIP mỗi lần", f"Đã mở: {Path(zips[0]).name}")
        else:
            self._go_mode("compress")
            n = self.compress_view.add_paths(valid)
            if n:
                self.notify("info", f"Đã thêm {n} mục")
        return True

    def on_ipc_received(self, action: str, paths: list[str]):
        """Được gọi từ luồng IPC; chuyển vào queue để xử lý an toàn trên luồng UI."""
        self.msg_queue.put(("ipc", action, list(paths)))

    def _handle_ipc(self, action: str, paths: list[str]):
        try:
            self.deiconify()
            self.lift()
            self.focus_force()
            self.attributes("-topmost", True)
            self.after(250, lambda: self.attributes("-topmost", False))
        except Exception:  # noqa: BLE001
            pass
        if paths:
            self._route_paths(action if action in ("compress", "extract") else None, paths, from_drop=False)

    # ------------------------------------------------------------------ Kéo & thả
    def _setup_drag_and_drop(self):
        if not HAS_DND or not hasattr(self, "drop_target_register"):
            return
        try:
            self.drop_target_register(DND_FILES)
            self.dnd_bind("<<DropEnter>>", self._on_drop_enter)
            self.dnd_bind("<<DropLeave>>", self._on_drop_leave)
            self.dnd_bind("<<Drop>>", self._on_files_dropped)
            logger.info("Đã đăng ký kéo thả (Drag & Drop).")
        except Exception as exc:  # noqa: BLE001
            logger.warning("Không thể đăng ký DnD: %s", exc)

    def _drop_zone(self):
        return getattr(self._current_view(), "drop", None) if self._stage in ("compress", "extract") else None

    def _on_drop_enter(self, event):
        z = self._drop_zone()
        if z is not None:
            z.set_state("dragging")
        return getattr(event, "action", "copy")

    def _on_drop_leave(self, event):
        z = self._drop_zone()
        if z is not None and z.state == "dragging":
            z.set_state("normal")
        return getattr(event, "action", "copy")

    def _flash_invalid(self):
        z = self._drop_zone()
        if z is None:
            return
        z.set_state("invalid")
        self.after(900, lambda: z.state == "invalid" and z.set_state("normal"))

    def _on_files_dropped(self, event):
        z = self._drop_zone()
        if z is not None and z.state == "dragging":
            z.set_state("normal")
        try:
            paths = parse_dropped_paths(event.data, self.tk.splitlist)
            ok = self._route_paths(None, paths, from_drop=True)
        except Exception as exc:  # noqa: BLE001 — dữ liệu thả lỗi không được làm crash app
            logger.warning("Dữ liệu kéo thả không hợp lệ: %s", exc)
            ok = False
        if not ok:
            self._flash_invalid()
            self.notify("warning", "Không đọc được dữ liệu vừa thả", "Hãy thử kéo lại hoặc dùng nút Chọn file.")
        return getattr(event, "action", "copy")

    # ------------------------------------------------------------------ Phím tắt
    def _setup_shortcuts(self):
        self.bind("<Control-o>", lambda e: self._current_view_call("pick_zip" if self.mode_switch.mode == "extract" else "pick_files"))
        self.bind("<Control-O>", lambda e: self._current_view_call("pick_folder"))
        self.bind("<Control-comma>", lambda e: self._open_settings())
        self.bind("<Control-h>", lambda e: self._open_history())
        self.bind("<Control-Key-1>", lambda e: self._go_mode("compress"))
        self.bind("<Control-Key-2>", lambda e: self._go_mode("extract"))
        self.bind("<Escape>", self._on_escape)
        self.bind("<Return>", self._on_return)

    def _current_view_call(self, method: str):
        if self._stage in ("compress", "extract"):
            fn = getattr(self._current_view(), method, None)
            if fn:
                fn()

    def _on_escape(self, _e=None):
        if self.is_working:
            self._request_cancel()
        elif self._stage == "result":
            self._close_result()

    def _on_return(self, e):
        # Enter kích hoạt hành động chính, trừ khi đang gõ trong ô nhập (ô nhập tự xử lý) hoặc đang ở nút
        if self._stage not in ("compress", "extract") or self.is_working:
            return
        w = e.widget
        if isinstance(w, (tk.Entry, tk.Text)):
            return
        self._current_view().start()

    # ------------------------------------------------------------------ Cửa sổ phụ
    def _open_history(self):
        if self._history_win is None or not self._history_win.winfo_exists():
            self._history_win = HistoryWindow(self)
        else:
            bring_to_front(self._history_win, self)

    def _open_settings(self):
        if self._settings_win is None or not self._settings_win.winfo_exists():
            self._settings_win = SettingsWindow(self, on_theme_change=self.apply_theme)
        else:
            bring_to_front(self._settings_win, self)

    def _open_about(self):
        if self._about_win is None or not self._about_win.winfo_exists():
            self._about_win = AboutWindow(self)
        else:
            bring_to_front(self._about_win, self)

    # ------------------------------------------------------------------ Chạy tác vụ (worker + queue)
    def _begin_task(self, op: str, verify: bool = False):
        self.is_working = True
        self._task_op = op
        self._task_verify = verify
        self._task_start = time.time()
        self.cancel_event.clear()
        self.progress_panel.start(op)
        self.compress_view.set_busy(True)
        self.extract_view.set_busy(True)
        self.mode_switch.set_enabled(False)
        self._show("progress")
        self.set_status("Đang nén..." if op == "compress" else "Đang giải nén...")

    def _start_compression(self, sources, output_path, level, password, verify):
        if self.is_working:
            return
        self._retry = lambda: self._start_compression(sources, output_path, level, password, verify)
        self._begin_task("compress", verify)

        def worker():
            res = compress_archive(
                sources=sources, output_path=output_path, level=level, password=password,
                verify=verify, cancel_event=self.cancel_event,
                progress_callback=lambda p: self.msg_queue.put(("progress", p)),
            )
            self.msg_queue.put(("result", res, sources))

        self.current_worker = threading.Thread(target=worker, daemon=True)
        self.current_worker.start()

    def _start_extraction(
        self, zip_path, dest_dir, password, policy: OverwritePolicy, members: Optional[list[str]] = None
    ):
        if self.is_working:
            return
        self._retry = lambda: self._start_extraction(zip_path, dest_dir, password, policy, members)
        self._begin_task("extract")
        # Giải nén chọn lọc (v2.1) đổi cách hiển thị trạng thái nhưng dùng chung 1 worker/core
        self.set_status(
            f"Đang giải nén {len(members)} mục đã chọn..." if members else "Đang giải nén..."
        )

        def worker():
            res = extract_archive(
                zip_path=zip_path, dest_dir=dest_dir, password=password, overwrite_policy=policy,
                cancel_event=self.cancel_event, members=members,
                progress_callback=lambda p: self.msg_queue.put(("progress", p)),
            )
            self.msg_queue.put(("result", res, [zip_path]))

        self.current_worker = threading.Thread(target=worker, daemon=True)
        self.current_worker.start()

    def _request_cancel(self):
        if not self.is_working or self.cancel_event.is_set():
            return
        if time.time() - self._task_start > CANCEL_CONFIRM_AFTER_S:
            if not messagebox.askyesno(
                "Hủy tác vụ?", "Tác vụ đã chạy một lúc. Bạn có chắc muốn hủy?", parent=self
            ):
                return
        self.cancel_event.set()
        self.progress_panel.set_cancelling()
        self.set_status("Đang hủy...")

    def _poll_queue(self):
        last_progress: Optional[ProgressInfo] = None
        try:
            while True:
                msg = self.msg_queue.get_nowait()
                kind = msg[0]
                if kind == "progress":
                    last_progress = msg[1]  # gộp: chỉ vẽ tiến trình mới nhất mỗi chu kỳ (throttle)
                elif kind == "result":
                    if last_progress is not None:
                        self._apply_progress(last_progress)
                        last_progress = None
                    self._handle_result(msg[1], msg[2])
                elif kind == "ipc":
                    self._handle_ipc(msg[1], msg[2])
        except queue.Empty:
            pass
        finally:
            if last_progress is not None and self.is_working:
                self._apply_progress(last_progress)
            self.after(POLL_MS, self._poll_queue)

    def _apply_progress(self, p: ProgressInfo):
        finalizing = "Đang xác minh file..." if (self._task_op == "compress" and self._task_verify) else None
        self.progress_panel.update_progress(p, finalizing_text=finalizing)

    # ------------------------------------------------------------------ Kết quả
    def _record_history(self, res: OperationResult, sources: list[str], status: str, err: Optional[str] = None):
        if not settings_service.get("history_enabled", True):
            return
        names = [Path(s).name for s in sources]
        summary = ", ".join(names[:3]) + (f" +{len(names) - 3}" if len(names) > 3 else "")
        history_service.add_record(
            operation=res.operation, input_summary=summary, output_path=res.output_path or "",
            file_count=res.file_count, original_size=res.original_size, final_size=res.compressed_size,
            elapsed_seconds=res.elapsed_seconds, status=status, error_message=err,  # tuyệt đối không ghi mật khẩu
        )

    def _finish_task(self):
        self.is_working = False
        self.compress_view.set_busy(False)
        self.extract_view.set_busy(False)
        self.mode_switch.set_enabled(True)

    def _back_to_input(self):
        self._show(self.mode_switch.mode)

    def _close_result(self):
        self._retry = None  # giải phóng mật khẩu giữ trong closure
        self._back_to_input()
        self.set_status("Sẵn sàng")

    def _handle_result(self, res: OperationResult, sources: list[str]):
        self._finish_task()
        op = res.operation

        if res.cancelled:
            self._retry = None
            self._record_history(res, sources, "cancelled")
            self._back_to_input()
            self.set_status("Đã hủy")
            self.notify("info", "Đã hủy tác vụ", "File tạm đã được dọn dẹp." if op == "compress" else "")
            return

        if not res.success:
            msg = friendly_error(res.error, res.error_details)
            self._record_history(res, sources, "error", msg)
            self.set_status("Có lỗi xảy ra")
            actions = [("Thử lại", "primary", self._do_retry), ("Đóng", "secondary", self._close_result)]
            self.result_panel.show_error(msg, res.error_details, actions)
            self._show("result")
            return

        self._retry = None
        self._record_history(res, sources, "success")
        self.set_status("Hoàn tất")
        out = res.output_path or ""
        if op == "compress":
            orig, final = res.original_size, res.compressed_size
            ratio = (1 - final / orig) * 100 if orig > 0 else 0
            size_line = f"{human_size(orig)} → {human_size(final)}"
            if ratio > 0:
                size_line = f"Giảm {ratio:.0f}% • " + size_line
            lines = [size_line, f"Thời gian: {format_duration(res.elapsed_seconds)}"]
            actions = [
                ("Mở file", "primary", lambda: self._open(open_file, out)),
                ("Mở thư mục", "secondary", lambda: self._open(open_in_explorer, out)),
                ("Nén tiếp", "secondary", self._compress_again),
                ("Đóng", "ghost", self._close_result),
            ]
            self.result_panel.show_success("Hoàn tất!", Path(out).name, lines, actions, res.warnings)
        else:
            lines = [
                f"Đã giải nén {res.file_count} mục",
                f"Thời gian: {format_duration(res.elapsed_seconds)}",
            ]
            actions = [
                ("Mở thư mục", "primary", lambda: self._open(open_in_explorer, out)),
                ("Giải nén tiếp", "secondary", self._extract_again),
                ("Đóng", "ghost", self._close_result),
            ]
            self.result_panel.show_success("Hoàn tất!", Path(out).name or out, lines, actions, res.warnings)
        self._show("result")

        if settings_service.get("open_folder_after_operation", True) and out:
            open_in_explorer(out)

    def _do_retry(self):
        if self._retry:
            retry = self._retry
            retry()

    def _open(self, fn, path: str):
        if not fn(path):
            self.notify("error", "Không thể mở", "File hoặc thư mục có thể đã bị di chuyển hoặc xóa.")

    def _compress_again(self):
        self._retry = None
        self.compress_view.reset()
        self._go_mode("compress")

    def _extract_again(self):
        self._retry = None
        self.extract_view.reset()
        self._go_mode("extract")

    # ------------------------------------------------------------------ Đóng cửa sổ
    def _on_close(self):
        if self.is_working:
            if not messagebox.askyesno(
                "Thoát VietZIP?", "Đang có tác vụ chạy. Thoát sẽ hủy tác vụ này. Bạn vẫn muốn thoát?", parent=self
            ):
                return
            self.cancel_event.set()
            if self.current_worker is not None:
                self.current_worker.join(timeout=3)  # để core kịp dọn file .tmp
        self.destroy()
