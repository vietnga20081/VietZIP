"""History window view."""

from __future__ import annotations

from pathlib import Path
from tkinter import messagebox
import customtkinter as ctk

from vietzip.services.history_service import history_service
from vietzip.ui.theme import (
    COLOR_CARD,
    COLOR_CARD_ALT,
    COLOR_BORDER,
    COLOR_BTN_OUTLINE_TEXT,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    BTN_SECONDARY_STYLE,
    FONT_MONO,
    FONT_REGULAR,
    FONT_SECTION,
    FONT_SMALL,
)
from vietzip.ui.widgets import setup_toplevel_window
from vietzip.utils.file_utils import get_asset_path, open_file, open_in_explorer
from vietzip.utils.format_utils import human_size


class HistoryWindow(ctk.CTkToplevel):
    """Cửa sổ xem và quản lý lịch sử các tác vụ."""

    def __init__(self, master):
        super().__init__(master)
        self.title("Lịch sử tác vụ — VietZIP")
        self.minsize(640, 400)
        setup_toplevel_window(self, master, 760, 520)

        ico_path = get_asset_path("vietzip.ico")
        if ico_path.exists():
            try:
                self.iconbitmap(str(ico_path))
            except Exception:
                pass

        self._build_layout()
        self._load_records()

    def _build_layout(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 8))
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header,
            text="🕘 Lịch sử nén & giải nén",
            font=FONT_SECTION,
            text_color=COLOR_TEXT_PRIMARY,
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkButton(
            header,
            text="🗑️ Xóa toàn bộ",
            width=115,
            height=30,
            **BTN_SECONDARY_STYLE,
            command=self._clear_all,
        ).grid(row=0, column=1, sticky="e")

        # Scrollable Record List
        self.list_frame = ctk.CTkScrollableFrame(
            self,
            corner_radius=12,
            border_width=1,
            border_color=COLOR_BORDER,
            fg_color=COLOR_CARD,
        )
        self.list_frame.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 14))
        self.list_frame.grid_columnconfigure(0, weight=1)

    def _load_records(self):
        for child in self.list_frame.winfo_children():
            child.destroy()

        records = history_service.get_records()

        if not records:
            empty_box = ctk.CTkFrame(self.list_frame, fg_color="transparent")
            empty_box.pack(pady=60)
            ctk.CTkLabel(
                empty_box,
                text="Chưa có lịch sử thao tác nào.",
                font=FONT_REGULAR,
                text_color=COLOR_TEXT_SECONDARY,
            ).pack()
            return

        for rec in records:
            card = ctk.CTkFrame(
                self.list_frame,
                corner_radius=8,
                fg_color=COLOR_CARD_ALT,
            )
            card.pack(fill="x", pady=4, padx=4)
            card.grid_columnconfigure(1, weight=1)

            # Icon op
            is_comp = rec.get("operation") == "compress"
            icon = "🗜️ Nén" if is_comp else "📂 Giải nén"
            status = rec.get("status", "success")

            status_color = "#10B981" if status == "success" else (
                "#EF4444" if status == "error" else "#F59E0B"
            )
            status_text = "✓ Thành công" if status == "success" else (
                "❌ Thất bại" if status == "error" else "⏹ Đã hủy"
            )

            # Left block: op + time
            left_box = ctk.CTkFrame(card, fg_color="transparent")
            left_box.grid(row=0, column=0, padx=12, pady=10, sticky="nw")

            ctk.CTkLabel(
                left_box,
                text=icon,
                font=FONT_SECTION,
                anchor="w",
            ).pack(anchor="w")

            ctk.CTkLabel(
                left_box,
                text=rec.get("timestamp", ""),
                font=FONT_SMALL,
                text_color=COLOR_TEXT_SECONDARY,
            ).pack(anchor="w")

            # Center block: paths & stats
            center_box = ctk.CTkFrame(card, fg_color="transparent")
            center_box.grid(row=0, column=1, padx=8, pady=8, sticky="w")

            out_path = rec.get("output_path", "")
            target_name = Path(out_path).name if out_path else "N/A"

            ctk.CTkLabel(
                center_box,
                text=f"Đích: {target_name}",
                font=FONT_REGULAR,
                anchor="w",
            ).pack(anchor="w")

            # Sizes
            orig_sz = rec.get("original_size", 0)
            final_sz = rec.get("final_size", 0)
            elapsed = rec.get("elapsed_seconds", 0)
            files = rec.get("file_count", 0)

            stats_str = f"{files} mục • {human_size(orig_sz)}"
            if is_comp and orig_sz > 0:
                ratio = max(0.0, (1 - final_sz / orig_sz) * 100)
                stats_str += f" ➜ {human_size(final_sz)} (giảm {ratio:.1f}%)"
            stats_str += f" • {elapsed}s"

            ctk.CTkLabel(
                center_box,
                text=stats_str,
                font=FONT_SMALL,
                text_color=COLOR_TEXT_SECONDARY,
                anchor="w",
            ).pack(anchor="w")

            # Right block: Status & Actions
            right_box = ctk.CTkFrame(card, fg_color="transparent")
            right_box.grid(row=0, column=2, padx=12, pady=8, sticky="e")

            ctk.CTkLabel(
                right_box,
                text=status_text,
                font=FONT_SMALL,
                text_color=status_color,
            ).pack(anchor="e", pady=(0, 4))

            # Buttons
            if out_path and Path(out_path).exists():
                act_row = ctk.CTkFrame(right_box, fg_color="transparent")
                act_row.pack(anchor="e")

                ctk.CTkButton(
                    act_row,
                    text="📂 Thư mục",
                    width=75,
                    height=24,
                    font=FONT_SMALL,
                    command=lambda p=out_path: open_in_explorer(p),
                ).pack(side="left", padx=(0, 4))

                if Path(out_path).is_file():
                    ctk.CTkButton(
                        act_row,
                        text="Mở file",
                        width=65,
                        height=24,
                        font=FONT_SMALL,
                        command=lambda p=out_path: open_file(p),
                    ).pack(side="left")

    def _clear_all(self):
        if messagebox.askyesno("Xác nhận", "Bạn có chắc muốn xóa toàn bộ lịch sử?", parent=self):
            history_service.clear()
            self._load_records()
