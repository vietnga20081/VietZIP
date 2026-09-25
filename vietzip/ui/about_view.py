"""Cửa sổ Giới thiệu: gọn, có Donate tùy chọn (thông tin giữ nguyên từ bản gốc)."""

from __future__ import annotations

import webbrowser

import customtkinter as ctk

from vietzip import __version__
from vietzip.ui.components import AppButton
from vietzip.ui.theme import (
    APP_NAME,
    APP_TAGLINE,
    COLOR_BG,
    COLOR_BORDER,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    FONT_BODY,
    FONT_SECTION,
    FONT_SMALL,
    FONT_TITLE,
    SP4,
    SP8,
    SP12,
    SP16,
    SP24,
)
from vietzip.ui.widgets import get_logo_image, setup_toplevel_window

WEBSITE_URL = "https://vietzip.vcp.io.vn"
GITHUB_URL = "https://github.com/vietnga20081/VietZIP"
DONATE_INFO = """Ủng hộ tác giả Team VietZIP:
- Ngân hàng: ACB
- Số tài khoản: 19675051
- Chủ tài khoản: DAO QUOC VIET
- Nội dung: VietZIP Donate
- Momo: 0816086555
- Website: https://vietzip.vcp.io.vn"""


class AboutWindow(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master, fg_color=COLOR_BG)
        self.title("Giới thiệu — VietZIP")
        self.resizable(False, False)
        setup_toplevel_window(self, master, 480, 560)
        self._build()

    def _divider(self, parent):
        ctk.CTkFrame(parent, height=1, fg_color=COLOR_BORDER).pack(fill="x", pady=SP16)

    def _build(self):
        box = ctk.CTkFrame(self, fg_color="transparent")
        box.pack(fill="both", expand=True, padx=SP24, pady=SP24)

        ctk.CTkLabel(box, text="", image=get_logo_image(72)).pack()
        ctk.CTkLabel(box, text=APP_NAME, font=FONT_TITLE, text_color=COLOR_TEXT_PRIMARY).pack(pady=(SP8, 0))
        ctk.CTkLabel(box, text=APP_TAGLINE, font=FONT_BODY, text_color=COLOR_TEXT_SECONDARY, wraplength=400).pack()
        ctk.CTkLabel(box, text=f"Phiên bản {__version__}", font=FONT_SMALL, text_color=COLOR_TEXT_MUTED).pack(pady=(SP4, SP12))

        row = ctk.CTkFrame(box, fg_color="transparent")
        row.pack()
        AppButton(row, text="GitHub", kind="secondary", command=lambda: webbrowser.open(GITHUB_URL)).pack(side="left", padx=SP4)
        AppButton(row, text="Website", kind="secondary", command=lambda: webbrowser.open(WEBSITE_URL)).pack(side="left", padx=SP4)

        self._divider(box)
        ctk.CTkLabel(
            box, text="Mã nguồn mở MIT  ·  Không quảng cáo  ·  Không thu phí bản quyền",
            font=FONT_SMALL, text_color=COLOR_TEXT_SECONDARY,
        ).pack()
        self._divider(box)

        ctk.CTkLabel(box, text="Ủng hộ Team VietZIP (tùy chọn)", font=FONT_SECTION, text_color=COLOR_TEXT_PRIMARY).pack()
        ctk.CTkLabel(
            box,
            text="Mỗi tách cà phê từ bạn là nguồn động lực quý báu giúp Team VietZIP duy trì hạ tầng máy chủ "
                 "và tiếp tục hoàn thiện các tính năng mới!\n\n"
                 "• Ngân hàng: ACB\n• Số tài khoản: 19675051\n• Chủ tài khoản: DAO QUOC VIET\n"
                 "• Nội dung: VietZIP Donate\n• Momo: 0816086555",
            font=FONT_SMALL, text_color=COLOR_TEXT_SECONDARY, justify="left", wraplength=400,
        ).pack(pady=(SP8, SP8))
        self.copy_btn = AppButton(box, text="Sao chép thông tin", kind="secondary", command=self._copy)
        self.copy_btn.pack()

        self._divider(box)
        ctk.CTkLabel(box, text="© 2026 Team VietZIP", font=FONT_SMALL, text_color=COLOR_TEXT_MUTED).pack()

    def _copy(self):
        self.clipboard_clear()
        self.clipboard_append(DONATE_INFO)
        self.copy_btn.configure(text="Đã sao chép")
        self.after(1800, lambda: self.copy_btn.winfo_exists() and self.copy_btn.configure(text="Sao chép thông tin"))
