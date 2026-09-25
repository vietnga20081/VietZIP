"""StatusBadge: nhãn trạng thái (không chỉ dựa vào màu — luôn có icon + chữ)."""

from __future__ import annotations

import customtkinter as ctk

from vietzip.ui.icons import get_icon
from vietzip.ui.theme import (
    COLOR_DANGER,
    COLOR_DANGER_SOFT,
    COLOR_SUCCESS,
    COLOR_SUCCESS_SOFT,
    COLOR_SURFACE_MUTED,
    COLOR_TEXT_SECONDARY,
    COLOR_WARNING,
    COLOR_WARNING_SOFT,
    FONT_SMALL,
)

_STATUS = {
    "success": ("Thành công", "check", COLOR_SUCCESS, COLOR_SUCCESS_SOFT),
    "error": ("Thất bại", "error", COLOR_DANGER, COLOR_DANGER_SOFT),
    "cancelled": ("Đã hủy", "close", COLOR_WARNING, COLOR_WARNING_SOFT),
    "warning": ("Cảnh báo", "warn", COLOR_WARNING, COLOR_WARNING_SOFT),
    "info": ("Thông tin", "info", COLOR_TEXT_SECONDARY, COLOR_SURFACE_MUTED),
}


class StatusBadge(ctk.CTkLabel):
    def __init__(
        self, master, status: str = "success", text: str | None = None, icon: str | None = None, **kwargs
    ):
        label, default_icon, fg, bg = _STATUS.get(status, _STATUS["info"])
        icon = icon or default_icon
        super().__init__(
            master,
            text=f" {text or label}",
            image=get_icon(icon, 14, fg),
            compound="left",
            font=FONT_SMALL,
            text_color=fg,
            fg_color=bg,
            corner_radius=8,
            padx=8,
            pady=2,
            **kwargs,
        )
