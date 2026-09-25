"""ProgressPanel: bảng tiến trình chính (thay cho progress bar nhỏ ở đáy)."""

from __future__ import annotations

from typing import Optional

import customtkinter as ctk

from vietzip.core.models import ProgressInfo
from vietzip.ui.components.icon_button import AppButton
from vietzip.ui.theme import (
    CARD_STYLE,
    COLOR_PRIMARY,
    COLOR_SURFACE_MUTED,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    FONT_BODY,
    FONT_HEADING,
    FONT_MONO,
    FONT_SMALL,
    FONT_TITLE,
    R_LG,
    SP4,
    SP16,
    SP24,
    SP32,
)
from vietzip.utils.format_utils import format_count, format_eta_human, format_speed, human_size, shorten_middle


class ProgressPanel(ctk.CTkFrame):
    def __init__(self, master, on_cancel):
        super().__init__(master, fg_color="transparent")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        card = ctk.CTkFrame(self, **{**CARD_STYLE, "corner_radius": R_LG})
        card.grid(row=0, column=0, padx=SP32, pady=SP24)
        card.grid_columnconfigure(0, weight=1)
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.grid(row=0, column=0, padx=SP32, pady=SP32)
        inner.grid_columnconfigure(0, weight=1)

        self.title = ctk.CTkLabel(inner, text="Đang xử lý...", font=FONT_HEADING, text_color=COLOR_TEXT_PRIMARY)
        self.title.grid(row=0, column=0, sticky="w")

        self.percent = ctk.CTkLabel(inner, text="0%", font=FONT_TITLE, text_color=COLOR_TEXT_PRIMARY)
        self.percent.grid(row=1, column=0, sticky="w", pady=(SP16, SP4))

        self.bar = ctk.CTkProgressBar(
            inner, height=14, corner_radius=7, progress_color=COLOR_PRIMARY, fg_color=COLOR_SURFACE_MUTED, width=460
        )
        self.bar.set(0)
        self.bar.grid(row=2, column=0, sticky="ew")

        self.current = ctk.CTkLabel(
            inner, text="", font=FONT_BODY, text_color=COLOR_TEXT_PRIMARY, anchor="w"
        )
        self.current.grid(row=3, column=0, sticky="w", pady=(SP16, 0))
        self.count = ctk.CTkLabel(inner, text="", font=FONT_SMALL, text_color=COLOR_TEXT_MUTED, anchor="w")
        self.count.grid(row=4, column=0, sticky="w")

        stats = ctk.CTkFrame(inner, fg_color="transparent")
        stats.grid(row=5, column=0, sticky="ew", pady=(SP16, 0))
        stats.grid_columnconfigure(1, weight=1)
        self.bytes_lbl = ctk.CTkLabel(stats, text="", font=FONT_MONO, text_color=COLOR_TEXT_SECONDARY)
        self.bytes_lbl.grid(row=0, column=0, sticky="w")
        self.speed_lbl = ctk.CTkLabel(stats, text="", font=FONT_MONO, text_color=COLOR_TEXT_SECONDARY)
        self.speed_lbl.grid(row=0, column=1)
        self.eta_lbl = ctk.CTkLabel(stats, text="", font=FONT_SMALL, text_color=COLOR_TEXT_SECONDARY)
        self.eta_lbl.grid(row=0, column=2, sticky="e")

        self.btn_cancel = AppButton(inner, text="Hủy", kind="secondary", width=120, command=on_cancel)
        self.btn_cancel.grid(row=6, column=0, pady=(SP24, 0))

        self._verb = "nén"
        self._cancelling = False

    def start(self, operation: str) -> None:
        """operation: 'compress' | 'extract'"""
        self._verb = "nén" if operation == "compress" else "giải nén"
        self._cancelling = False
        self.title.configure(text=f"Đang {self._verb}...")
        self.percent.configure(text="0%")
        self.bar.set(0)
        self.current.configure(text="Đang chuẩn bị...")
        self.count.configure(text="")
        self.bytes_lbl.configure(text="")
        self.speed_lbl.configure(text="")
        self.eta_lbl.configure(text="")
        self.btn_cancel.configure(state="normal", text="Hủy")

    def update_progress(self, p: ProgressInfo, finalizing_text: Optional[str] = None) -> None:
        if self._cancelling:
            return
        pct = max(0.0, min(1.0, p.percent))
        self.bar.set(pct)
        self.percent.configure(text=f"{int(pct * 100)}%")
        name = p.current_file.replace("\\", "/").rstrip("/").split("/")[-1] or p.current_file
        self.current.configure(text=shorten_middle(name, 60))
        self.count.configure(text=f"Mục {format_count(p.current_index)} / {format_count(p.total_files)}")
        self.bytes_lbl.configure(text=f"{human_size(p.processed_bytes)} / {human_size(p.total_bytes)}")
        self.speed_lbl.configure(text=format_speed(p.speed_bps))
        if finalizing_text and pct >= 0.999:
            self.eta_lbl.configure(text=finalizing_text)
        else:
            self.eta_lbl.configure(text=format_eta_human(p.eta_seconds))

    def set_cancelling(self) -> None:
        self._cancelling = True
        self.title.configure(text="Đang hủy...")
        self.eta_lbl.configure(text="Đang dọn dẹp file tạm")
        self.btn_cancel.configure(state="disabled")
