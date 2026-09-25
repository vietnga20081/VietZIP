"""Toast chuẩn hóa 4 loại: success / warning / error / info."""

from __future__ import annotations

from typing import Callable, Optional, Sequence

import customtkinter as ctk

from vietzip.ui.components.icon_button import AppButton, IconButton
from vietzip.ui.icons import get_icon
from vietzip.ui.theme import (
    COLOR_BORDER,
    COLOR_DANGER,
    COLOR_SUCCESS,
    COLOR_SURFACE_ELEVATED,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    COLOR_WARNING,
    FONT_SECTION,
    FONT_SMALL,
    R_MD,
    SP4,
    SP8,
    SP12,
    SP16,
)

_KIND = {
    "success": ("check_circle", COLOR_SUCCESS, 6000),
    "warning": ("warn", COLOR_WARNING, 9000),
    "error": ("error", COLOR_DANGER, 15000),   # lỗi quan trọng ở lại lâu hơn
    "info": ("info", COLOR_TEXT_SECONDARY, 4000),
}
MAX_TOASTS = 3


class Toast(ctk.CTkFrame):
    def __init__(self, master, kind, title, message, actions, on_close):
        icon, color, self.duration = _KIND[kind]
        super().__init__(
            master, corner_radius=R_MD, border_width=1, border_color=COLOR_BORDER, fg_color=COLOR_SURFACE_ELEVATED
        )
        self._on_close = on_close
        self.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(self, text="", image=get_icon(icon, 22, color)).grid(
            row=0, column=0, rowspan=2, padx=(SP12, SP8), pady=SP12, sticky="n"
        )
        ctk.CTkLabel(self, text=title, font=FONT_SECTION, text_color=COLOR_TEXT_PRIMARY, anchor="w").grid(
            row=0, column=1, sticky="w", pady=(SP12, 0)
        )
        IconButton(self, icon="close", tooltip="Đóng", size=26, icon_size=12, command=self.dismiss).grid(
            row=0, column=2, padx=(SP4, SP8), pady=(SP8, 0), sticky="ne"
        )
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.grid(row=1, column=1, columnspan=2, sticky="ew", padx=(0, SP12), pady=(0, SP12))
        if message:
            ctk.CTkLabel(
                body, text=message, font=FONT_SMALL, text_color=COLOR_TEXT_SECONDARY,
                justify="left", anchor="w", wraplength=300,
            ).pack(anchor="w")
        if actions:
            row = ctk.CTkFrame(body, fg_color="transparent")
            row.pack(anchor="w", pady=(SP8, 0))
            for i, (label, cb) in enumerate(actions):
                AppButton(
                    row, text=label, kind="secondary", height=28, font=FONT_SMALL,
                    command=lambda c=cb: (c(), self.dismiss()),
                ).pack(side="left", padx=(0, SP8))
        self._job = self.after(self.duration, self.dismiss)

    def dismiss(self):
        if self._job:
            try:
                self.after_cancel(self._job)
            except Exception:
                pass
            self._job = None
        try:
            self.destroy()
        finally:
            self._on_close(self)


class ToastManager:
    """Quản lý hàng toast ở góc trên bên phải (không che nút hành động chính ở đáy)."""

    def __init__(self, root, top_offset: int = 84):
        self.root = root
        self.top_offset = top_offset
        self.toasts: list[Toast] = []

    def show(
        self,
        kind: str,
        title: str,
        message: str = "",
        actions: Optional[Sequence[tuple[str, Callable[[], None]]]] = None,
    ) -> None:
        while len(self.toasts) >= MAX_TOASTS:
            self.toasts[0].dismiss()
        toast = Toast(self.root, kind, title, message, actions or [], self._closed)
        self.toasts.append(toast)
        self._layout()

    def _closed(self, toast: Toast):
        if toast in self.toasts:
            self.toasts.remove(toast)
        self._layout()

    def _layout(self):
        y = self.top_offset
        for t in self.toasts:
            try:
                t.update_idletasks()
                t.place(relx=1.0, x=-SP16, y=y, anchor="ne")
                t.lift()
                y += t.winfo_reqheight() + SP8
            except Exception:
                pass
