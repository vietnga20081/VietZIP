"""Custom UI widgets: Toast notifications, OverwriteDialog, DropZone, etc."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Callable, Optional
import customtkinter as ctk

from vietzip.core.models import OverwritePolicy
from vietzip.ui.theme import (
    COLOR_CARD,
    COLOR_BORDER,
    COLOR_PRIMARY,
    COLOR_PRIMARY_HOVER,
    COLOR_BTN_OUTLINE_TEXT,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    BTN_SECONDARY_STYLE,
    FONT_REGULAR,
    FONT_SECTION,
    FONT_SMALL,
)
from vietzip.utils.file_utils import open_file, open_in_explorer


def bring_to_front(window: ctk.CTkToplevel, master=None):
    """Đảm bảo cửa sổ toplevel luôn nổi lên phía trước master, không bị ẩn và nhận focus."""
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


def setup_toplevel_window(
    window: ctk.CTkToplevel,
    master=None,
    width: int = 540,
    height: int = 500,
):
    """Cấu hình cửa sổ toplevel: căn giữa theo master (hoặc màn hình), gán transient và đưa lên trước."""
    try:
        if master is not None and hasattr(master, "winfo_exists") and master.winfo_exists():
            window.transient(master)
            master.update_idletasks()
            mx = master.winfo_x()
            my = master.winfo_y()
            mw = master.winfo_width()
            mh = master.winfo_height()
            x = max(0, mx + (mw - width) // 2)
            y = max(0, my + (mh - height) // 2)
        else:
            sw = window.winfo_screenwidth()
            sh = window.winfo_screenheight()
            x = max(0, (sw - width) // 2)
            y = max(0, (sh - height) // 2)

        window.geometry(f"{width}x{height}+{x}+{y}")
    except Exception:
        window.geometry(f"{width}x{height}")

    bring_to_front(window, master)


class ToastNotification(ctk.CTkFrame):
    """Toast popup thông báo kết quả thao tác gọn gàng, không làm gián đoạn người dùng."""

    def __init__(
        self,
        master,
        title: str,
        message: str,
        target_path: Optional[str] = None,
        duration_ms: int = 7000,
        **kwargs,
    ):
        super().__init__(
            master,
            corner_radius=12,
            border_width=1,
            border_color=COLOR_BORDER,
            fg_color=COLOR_CARD,
            **kwargs,
        )
        self.target_path = target_path
        self._dismiss_job = None

        self.grid_columnconfigure(0, weight=1)

        # Header
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=12, pady=(10, 4))
        header_frame.grid_columnconfigure(0, weight=1)

        title_lbl = ctk.CTkLabel(
            header_frame, text=title, font=FONT_SECTION, anchor="w", text_color=COLOR_TEXT_PRIMARY
        )
        title_lbl.grid(row=0, column=0, sticky="w")

        close_btn = ctk.CTkButton(
            header_frame,
            text="✕",
            width=22,
            height=22,
            fg_color="transparent",
            text_color=COLOR_TEXT_SECONDARY,
            hover_color=("gray80", "gray25"),
            command=self.dismiss,
        )
        close_btn.grid(row=0, column=1, sticky="e")

        # Message
        msg_lbl = ctk.CTkLabel(
            self,
            text=message,
            font=FONT_REGULAR,
            anchor="w",
            justify="left",
            wraplength=340,
            text_color=COLOR_TEXT_SECONDARY,
        )
        msg_lbl.grid(row=1, column=0, sticky="w", padx=12, pady=(0, 8))

        # Action Buttons
        if target_path and Path(target_path).exists():
            btn_frame = ctk.CTkFrame(self, fg_color="transparent")
            btn_frame.grid(row=2, column=0, sticky="ew", padx=12, pady=(0, 10))

            p = Path(target_path)
            if p.is_file():
                open_f_btn = ctk.CTkButton(
                    btn_frame,
                    text="📦 Mở file",
                    width=90,
                    height=28,
                    font=FONT_SMALL,
                    command=lambda: open_file(p),
                )
                open_f_btn.pack(side="left", padx=(0, 8))

            open_dir_btn = ctk.CTkButton(
                btn_frame,
                text="📂 Mở thư mục",
                width=100,
                height=28,
                font=FONT_SMALL,
                **BTN_SECONDARY_STYLE,
                command=lambda: open_in_explorer(p),
            )
            open_dir_btn.pack(side="left")

        # Auto dismiss
        self._dismiss_job = self.after(duration_ms, self.dismiss)

    def dismiss(self):
        """Đóng toast."""
        if self._dismiss_job:
            self.after_cancel(self._dismiss_job)
            self._dismiss_job = None
        self.destroy()


class OverwriteDialog(ctk.CTkToplevel):
    """Hộp thoại xác nhận ghi đè file khi giải nén."""

    def __init__(self, master, file_path: Path):
        super().__init__(master)
        self.title("File đã tồn tại")
        self.resizable(False, False)
        setup_toplevel_window(self, master, 450, 260)
        self.attributes("-topmost", True)

        self.selected_policy = OverwritePolicy.AUTO_RENAME
        self.apply_to_all = False
        self.cancelled = False

        self.grid_columnconfigure(0, weight=1)

        # Title
        ctk.CTkLabel(
            self,
            text="⚠️ Phát hiện file đã tồn tại",
            font=FONT_SECTION,
            text_color=COLOR_TEXT_PRIMARY,
        ).pack(pady=(16, 6))

        # File name
        ctk.CTkLabel(
            self,
            text=f"File: {file_path.name}\n({file_path})",
            font=FONT_SMALL,
            wraplength=410,
            text_color=COLOR_TEXT_SECONDARY,
        ).pack(pady=(0, 12))

        # Options
        self.policy_var = ctk.StringVar(value=OverwritePolicy.AUTO_RENAME.value)

        opt_frame = ctk.CTkFrame(self, fg_color="transparent")
        opt_frame.pack(padx=20, fill="x")

        ctk.CTkRadioButton(
            opt_frame,
            text="Tự động đổi tên (Ví dụ: file (1).ext)",
            variable=self.policy_var,
            value=OverwritePolicy.AUTO_RENAME.value,
            text_color=COLOR_TEXT_PRIMARY,
        ).pack(anchor="w", pady=3)

        ctk.CTkRadioButton(
            opt_frame,
            text="Ghi đè file cũ",
            variable=self.policy_var,
            value=OverwritePolicy.OVERWRITE.value,
            text_color=COLOR_TEXT_PRIMARY,
        ).pack(anchor="w", pady=3)

        ctk.CTkRadioButton(
            opt_frame,
            text="Bỏ qua (không giải nén file này)",
            variable=self.policy_var,
            value=OverwritePolicy.SKIP.value,
            text_color=COLOR_TEXT_PRIMARY,
        ).pack(anchor="w", pady=3)

        self.apply_all_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            self,
            text="Áp dụng cho tất cả các file trùng lặp còn lại",
            variable=self.apply_all_var,
            font=FONT_SMALL,
            text_color=COLOR_TEXT_PRIMARY,
        ).pack(anchor="w", padx=24, pady=10)

        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(4, 12))

        ctk.CTkButton(
            btn_frame,
            text="Tiếp tục",
            width=100,
            command=self._on_confirm,
        ).pack(side="right", padx=(8, 0))

        ctk.CTkButton(
            btn_frame,
            text="Hủy tác vụ",
            width=100,
            **BTN_SECONDARY_STYLE,
            command=self._on_cancel,
        ).pack(side="right")

        # Modal wait
        self.grab_set()
        self.wait_window()

    def _on_confirm(self):
        self.selected_policy = OverwritePolicy(self.policy_var.get())
        self.apply_to_all = self.apply_all_var.get()
        self.destroy()

    def _on_cancel(self):
        self.cancelled = True
        self.destroy()
