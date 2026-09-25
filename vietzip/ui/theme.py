"""Design tokens của VietZIP: màu, spacing, bo góc, font và style widget dùng chung.

Mọi view/component phải lấy giá trị từ đây, không hard-code màu hay khoảng cách.
Màu là tuple (Light, Dark) để CustomTkinter tự đổi theo chế độ hiển thị.
"""

from __future__ import annotations

import customtkinter as ctk

# ------------------------------------------------------------------ Thương hiệu
APP_NAME = "VietZIP"
APP_SUBTITLE = "Nén & giải nén đơn giản"
APP_TAGLINE = "Nén & giải nén đơn giản, an toàn và thần tốc"

# ------------------------------------------------------------------ Spacing (px)
SP4, SP8, SP12, SP16, SP20, SP24, SP32, SP40, SP48 = 4, 8, 12, 16, 20, 24, 32, 40, 48

# ------------------------------------------------------------------ Bo góc
R_SM = 8
R_MD = 12
R_LG = 16
R_DIALOG = 20

# ------------------------------------------------------------------ Màu (Light, Dark)
COLOR_BG = ("#F4F6F9", "#0E1420")
COLOR_SURFACE = ("#FFFFFF", "#172033")
COLOR_SURFACE_ELEVATED = ("#FFFFFF", "#1F2A40")
COLOR_SURFACE_MUTED = ("#EEF2F6", "#1B2538")
COLOR_BORDER = ("#D9E0E8", "#2A3650")
COLOR_BORDER_STRONG = ("#B6C2D0", "#3B4A68")
COLOR_DROP_BORDER = ("#8FA0B5", "#54648A")
COLOR_DISABLED_FILL = ("#D5DCE5", "#2B3750")
COLOR_DISABLED_TEXT = ("#6B7A8F", "#8593AA")

COLOR_TEXT_PRIMARY = ("#0F172A", "#F1F5F9")
COLOR_TEXT_SECONDARY = ("#475569", "#A9B5C8")
COLOR_TEXT_MUTED = ("#64748B", "#8593AA")
COLOR_TEXT_ON_PRIMARY = ("#FFFFFF", "#FFFFFF")

# Primary duy nhất toàn app (đủ tương phản với chữ trắng)
COLOR_PRIMARY = ("#047857", "#047857")
COLOR_PRIMARY_HOVER = ("#065F46", "#059669")
COLOR_PRIMARY_SOFT = ("#E3F5EE", "#10362C")

# Trạng thái — chỉ dùng đúng ngữ cảnh
COLOR_SUCCESS = ("#047857", "#34D399")
COLOR_SUCCESS_SOFT = ("#E3F5EE", "#10362C")
COLOR_WARNING = ("#B45309", "#FBBF24")
COLOR_WARNING_SOFT = ("#FEF3C7", "#3A2F12")
COLOR_DANGER = ("#B91C1C", "#F87171")
COLOR_DANGER_SOFT = ("#FEE2E2", "#3B1A1F")
COLOR_DANGER_FILL = ("#DC2626", "#DC2626")
COLOR_DANGER_FILL_HOVER = ("#B91C1C", "#B91C1C")
COLOR_FOCUS = ("#2563EB", "#60A5FA")

# ------------------------------------------------------------------ Typography
FONT_FAMILY = "Segoe UI"
FONT_TITLE = (FONT_FAMILY, 20, "bold")
FONT_HEADING = (FONT_FAMILY, 16, "bold")
FONT_SECTION = (FONT_FAMILY, 13, "bold")
FONT_BODY = (FONT_FAMILY, 13)
FONT_SMALL = (FONT_FAMILY, 11)
FONT_BUTTON_LG = (FONT_FAMILY, 15, "bold")
FONT_MONO = ("Consolas", 11)

# ------------------------------------------------------------------ Style widget
BUTTON_STYLES: dict[str, dict] = {
    "primary": dict(
        fg_color=COLOR_PRIMARY,
        hover_color=COLOR_PRIMARY_HOVER,
        text_color=COLOR_TEXT_ON_PRIMARY,
        text_color_disabled=("#E5E7EB", "#94A3B8"),
        border_width=0,
    ),
    "secondary": dict(
        fg_color=COLOR_SURFACE,
        hover_color=COLOR_SURFACE_MUTED,
        text_color=COLOR_TEXT_PRIMARY,
        text_color_disabled=COLOR_TEXT_MUTED,
        border_width=1,
        border_color=COLOR_BORDER_STRONG,
    ),
    "ghost": dict(
        fg_color="transparent",
        hover_color=COLOR_SURFACE_MUTED,
        text_color=COLOR_TEXT_SECONDARY,
        text_color_disabled=COLOR_TEXT_MUTED,
        border_width=0,
    ),
    "danger": dict(
        fg_color=COLOR_DANGER_FILL,
        hover_color=COLOR_DANGER_FILL_HOVER,
        text_color=COLOR_TEXT_ON_PRIMARY,
        text_color_disabled=("#FEE2E2", "#FCA5A5"),
        border_width=0,
    ),
}

ENTRY_STYLE = dict(
    fg_color=COLOR_SURFACE,
    border_color=COLOR_BORDER_STRONG,
    border_width=1,
    text_color=COLOR_TEXT_PRIMARY,
    placeholder_text_color=COLOR_TEXT_MUTED,
    corner_radius=R_SM,
    height=36,
    font=FONT_BODY,
)

CHECKBOX_STYLE = dict(
    fg_color=COLOR_PRIMARY,
    hover_color=COLOR_PRIMARY_HOVER,
    border_color=COLOR_BORDER_STRONG,
    text_color=COLOR_TEXT_PRIMARY,
    checkmark_color="#FFFFFF",
    font=FONT_BODY,
    corner_radius=6,
)

RADIO_STYLE = dict(
    fg_color=COLOR_PRIMARY,
    hover_color=COLOR_PRIMARY_HOVER,
    border_color=COLOR_BORDER_STRONG,
    text_color=COLOR_TEXT_PRIMARY,
    font=FONT_BODY,
)

SWITCH_STYLE = dict(
    progress_color=COLOR_PRIMARY,
    button_color=("#FFFFFF", "#E2E8F0"),
    button_hover_color=("#F1F5F9", "#FFFFFF"),
    fg_color=("#CBD5E1", "#334155"),
    text_color=COLOR_TEXT_PRIMARY,
    font=FONT_BODY,
)

OPTION_STYLE = dict(
    fg_color=COLOR_SURFACE,
    button_color=COLOR_SURFACE_MUTED,
    button_hover_color=COLOR_BORDER,
    text_color=COLOR_TEXT_PRIMARY,
    dropdown_fg_color=COLOR_SURFACE_ELEVATED,
    dropdown_text_color=COLOR_TEXT_PRIMARY,
    dropdown_hover_color=COLOR_SURFACE_MUTED,
    corner_radius=R_SM,
    height=36,
    font=FONT_BODY,
    dropdown_font=FONT_BODY,
)

CARD_STYLE = dict(
    fg_color=COLOR_SURFACE,
    border_width=1,
    border_color=COLOR_BORDER,
    corner_radius=R_MD,
)


# ------------------------------------------------------------------ Helper
def init_theme(appearance_mode: str = "System") -> None:
    """Khởi tạo chế độ hiển thị (System / Light / Dark)."""
    ctk.set_appearance_mode(appearance_mode)
    ctk.set_default_color_theme("green")


def resolve_color(color: tuple[str, str] | str) -> str:
    """Trả về mã màu thực theo chế độ Light/Dark hiện tại (cho widget tk thuần)."""
    if isinstance(color, str):
        return color
    return color[1] if ctk.get_appearance_mode() == "Dark" else color[0]
