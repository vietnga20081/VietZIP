"""Theme configuration, colors, and mascot states for VietZIP."""

from __future__ import annotations

import customtkinter as ctk

# Tên ứng dụng và Mascot
APP_NAME = "VietZIP"
APP_SUBTITLE = "Nén & giải nén đơn giản, an toàn và thần tốc ✨"

MASCOT_IDLE = ["📦", "🐼", "🧧", "🎋"]
MASCOT_WORKING = ["⚙️", "🌀", "✨", "🚀"]
MASCOT_SUCCESS = ["🎉", "✅", "🥳", "🏆"]
MASCOT_ERROR = ["😿", "❌", "⚠️"]
MASCOT_CANCELLED = ["😐", "⏹️"]

# Fonts
FONT_TITLE = ("Segoe UI", 24, "bold")
FONT_SUBTITLE = ("Segoe UI", 12)
FONT_SECTION = ("Segoe UI", 14, "bold")
FONT_REGULAR = ("Segoe UI", 13)
FONT_SMALL = ("Segoe UI", 11)
FONT_MONO = ("Consolas", 11)

# Color Palette (Light, Dark)
COLOR_BG = ("#F7F9FC", "#111827")
COLOR_CARD = ("#FFFFFF", "#1F2937")
COLOR_CARD_ALT = ("#F1F5F9", "#1E293B")
COLOR_BORDER = ("#CBD5E1", "#374151")

COLOR_PRIMARY = ("#10B981", "#059669")         # Emerald Green
COLOR_PRIMARY_HOVER = ("#059669", "#047857")
COLOR_SECONDARY = ("#E0E7FF", "#312E81")
COLOR_TEXT_PRIMARY = ("#0F172A", "#F8FAFC")      # Đậm rõ nét trên nền sáng
COLOR_TEXT_SECONDARY = ("#334155", "#94A3B8")    # Slate đậm tương phản cao
COLOR_BTN_TEXT = ("#FFFFFF", "#FFFFFF")
COLOR_BTN_OUTLINE_TEXT = ("#0F172A", "#F8FAFC")  # Chữ nút viền/trong suốt
COLOR_SEGMENT_TEXT = ("#0F172A", "#F8FAFC")
COLOR_DANGER = ("#EF4444", "#DC2626")
COLOR_DANGER_HOVER = ("#DC2626", "#B91C1C")
COLOR_WARNING = ("#F59E0B", "#D97706")

# Kiểu dáng nút phụ / nút viền (Secondary Button Style) tương phản cao
BTN_SECONDARY_STYLE = {
    "fg_color": ("#FFFFFF", "#1E293B"),
    "border_color": ("#CBD5E1", "#475569"),
    "border_width": 1,
    "text_color": ("#0F172A", "#F8FAFC"),
    "hover_color": ("#E2E8F0", "#334155"),
}


def init_theme(appearance_mode: str = "System"):
    """Khởi tạo chế độ hiển thị CustomTkinter và tinh chỉnh tương phản giao diện sáng."""
    ctk.set_appearance_mode(appearance_mode)
    ctk.set_default_color_theme("green")

    # Tinh chỉnh theme gốc để SegmentedButton và Tabview có chữ đậm rõ nét ở Light mode
    try:
        ctk.ThemeManager.theme["CTkSegmentedButton"]["text_color"] = ["#0F172A", "#F8FAFC"]
        ctk.ThemeManager.theme["CTkSegmentedButton"]["unselected_color"] = ["#E2E8F0", "gray29"]
        ctk.ThemeManager.theme["CTkSegmentedButton"]["unselected_hover_color"] = ["#CBD5E1", "gray41"]
    except Exception:
        pass
