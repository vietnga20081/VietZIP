"""About window view for VietZIP."""

from __future__ import annotations

import sys
import webbrowser
from pathlib import Path
from tkinter import messagebox
import customtkinter as ctk

from vietzip.ui.theme import (
    APP_NAME,
    APP_SUBTITLE,
    COLOR_CARD,
    COLOR_BORDER,
    COLOR_PRIMARY,
    COLOR_PRIMARY_HOVER,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    BTN_SECONDARY_STYLE,
    FONT_TITLE,
    FONT_SECTION,
    FONT_REGULAR,
    FONT_SMALL,
    FONT_MONO,
)
from vietzip.ui.widgets import setup_toplevel_window
from vietzip.utils.file_utils import get_asset_path


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
    """Cửa sổ Giới thiệu Team VietZIP, cam kết miễn phí và Donate."""

    def __init__(self, master):
        super().__init__(master)
        self.title("Giới thiệu — VietZIP")
        self.minsize(500, 480)
        self.resizable(False, False)
        setup_toplevel_window(self, master, 560, 540)

        # Set window icon
        ico_path = get_asset_path("vietzip.ico")
        if ico_path.exists():
            try:
                self.iconbitmap(str(ico_path))
            except Exception:
                pass

        self._build_layout()

    def _build_layout(self):
        self.grid_columnconfigure(0, weight=1)

        # Main scrollable container
        container = ctk.CTkScrollableFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=20, pady=16)

        # 1. Header with Logo & Title
        header_frame = ctk.CTkFrame(container, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 14))

        logo_path = get_asset_path("icon-VietZIP.png")
        self.logo_img = None
        if logo_path.exists():
            try:
                from PIL import Image
                pil_img = Image.open(logo_path)
                self.logo_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(60, 60))
            except Exception:
                pass

        if self.logo_img:
            logo_lbl = ctk.CTkLabel(header_frame, text="", image=self.logo_img, width=60, height=60)
        else:
            logo_lbl = ctk.CTkLabel(header_frame, text="🗜️", font=("Segoe UI Emoji", 42))
        logo_lbl.pack(side="left", padx=(0, 14))

        title_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_box.pack(side="left", fill="y", expand=True)

        ctk.CTkLabel(
            title_box,
            text=f"{APP_NAME} v2.0.0",
            font=FONT_TITLE,
            text_color=COLOR_TEXT_PRIMARY,
            anchor="w",
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_box,
            text=APP_SUBTITLE,
            font=FONT_REGULAR,
            text_color=COLOR_TEXT_SECONDARY,
            anchor="w",
        ).pack(anchor="w")

        # Free Badge
        badge = ctk.CTkLabel(
            title_box,
            text="✨ 100% MIỄN PHÍ • MÃ NGUỒN MỞ",
            font=("Segoe UI", 10, "bold"),
            text_color="#0284C7",
            fg_color=("#E0F2FE", "gray20"),
            corner_radius=6,
            padx=8,
            pady=2,
        )
        badge.pack(anchor="w", pady=(4, 0))

        # 2. Team & Triết lý
        card_intro = ctk.CTkFrame(
            container,
            corner_radius=10,
            border_width=1,
            border_color=COLOR_BORDER,
            fg_color=COLOR_CARD,
        )
        card_intro.pack(fill="x", pady=(0, 12), padx=2)

        ctk.CTkLabel(
            card_intro,
            text="👥 Về Team VietZIP & Triết lý",
            font=FONT_SECTION,
            text_color=COLOR_TEXT_PRIMARY,
            anchor="w",
        ).pack(fill="x", padx=14, pady=(10, 4))

        intro_text = (
            "VietZIP được xây dựng và duy trì bởi Team VietZIP với mục tiêu "
            "mang lại trải nghiệm nén & giải nén file hiện đại, nhanh chóng, "
            "bảo mật và thân thiện nhất cho người dùng Việt Nam.\n\n"
            "• Hoàn toàn miễn phí trọn đời cho mọi cá nhân & tổ chức.\n"
            "• Không quảng cáo, không mã độc, không thu thập dữ liệu cá nhân."
        )
        ctk.CTkLabel(
            card_intro,
            text=intro_text,
            font=FONT_REGULAR,
            text_color=COLOR_TEXT_SECONDARY,
            justify="left",
            wraplength=480,
            anchor="w",
        ).pack(fill="x", padx=14, pady=(0, 12))

        # 3. Liên kết Website & GitHub
        card_links = ctk.CTkFrame(
            container,
            corner_radius=10,
            border_width=1,
            border_color=COLOR_BORDER,
            fg_color=COLOR_CARD,
        )
        card_links.pack(fill="x", pady=(0, 12), padx=2)

        ctk.CTkLabel(
            card_links,
            text="🌐 Kênh chính thức & Tải về",
            font=FONT_SECTION,
            text_color=COLOR_TEXT_PRIMARY,
            anchor="w",
        ).pack(fill="x", padx=14, pady=(10, 4))

        btn_row = ctk.CTkFrame(card_links, fg_color="transparent")
        btn_row.pack(fill="x", padx=14, pady=(4, 12))

        ctk.CTkButton(
            btn_row,
            text="🌐 Website vietzip.vcp.io.vn",
            command=lambda: webbrowser.open(WEBSITE_URL),
            height=32,
            fg_color=COLOR_PRIMARY,
            hover_color=COLOR_PRIMARY_HOVER,
        ).pack(side="left", padx=(0, 8), fill="x", expand=True)

        ctk.CTkButton(
            btn_row,
            text="⭐ GitHub Repository",
            command=lambda: webbrowser.open(GITHUB_URL),
            height=32,
            **BTN_SECONDARY_STYLE,
        ).pack(side="left", fill="x", expand=True)

        # 4. Donate & Ủng hộ tác giả
        card_donate = ctk.CTkFrame(
            container,
            corner_radius=10,
            border_width=1,
            border_color=COLOR_BORDER,
            fg_color=COLOR_CARD,
        )
        card_donate.pack(fill="x", pady=(0, 12), padx=2)

        ctk.CTkLabel(
            card_donate,
            text="☕ Ủng hộ tác giả (Donate)",
            font=FONT_SECTION,
            text_color=COLOR_TEXT_PRIMARY,
            anchor="w",
        ).pack(fill="x", padx=14, pady=(10, 4))

        donate_desc = (
            "Mỗi tách cà phê từ bạn là nguồn động lực quý báu giúp Team VietZIP "
            "duy trì hạ tầng máy chủ và tiếp tục hoàn thiện các tính năng mới!\n\n"
            "• Ngân hàng: ACB\n"
            "• Số tài khoản: 19675051\n"
            "• Chủ tài khoản: DAO QUOC VIET\n"
            "• Nội dung: VietZIP Donate\n"
            "• Momo: 0816086555"
        )
        ctk.CTkLabel(
            card_donate,
            text=donate_desc,
            font=FONT_REGULAR,
            text_color=COLOR_TEXT_SECONDARY,
            justify="left",
            wraplength=480,
            anchor="w",
        ).pack(fill="x", padx=14, pady=(0, 8))

        ctk.CTkButton(
            card_donate,
            text="📋 Sao chép thông tin Donate",
            height=30,
            **BTN_SECONDARY_STYLE,
            command=self._copy_donate_info,
        ).pack(anchor="w", padx=14, pady=(0, 12))

        # Bottom Close Button
        ctk.CTkButton(
            self,
            text="Đóng",
            width=90,
            height=32,
            **BTN_SECONDARY_STYLE,
            command=self.destroy,
        ).pack(side="bottom", pady=10)

    def _copy_donate_info(self):
        """Sao chép thông tin donate vào clipboard."""
        self.clipboard_clear()
        self.clipboard_append(DONATE_INFO)
        messagebox.showinfo(
            "Đã sao chép! — VietZIP",
            "Đã sao chép thông tin Donate vào bộ nhớ tạm (Clipboard).\n\n"
            "Cảm ơn bạn rất nhiều vì đã đồng hành và ủng hộ Team VietZIP! 💖",
            parent=self,
        )
