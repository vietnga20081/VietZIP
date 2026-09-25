"""FileList + FileListItem: danh sách nguồn cần nén (có giới hạn render để không lag)."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import customtkinter as ctk

from vietzip.ui.components.icon_button import AppButton, IconButton
from vietzip.ui.components.tooltip import Tooltip
from vietzip.ui.icons import get_icon
from vietzip.ui.theme import (
    CARD_STYLE,
    COLOR_SURFACE_MUTED,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    FONT_BODY,
    FONT_SECTION,
    FONT_SMALL,
    R_SM,
    SP4,
    SP8,
    SP12,
)
from vietzip.utils.format_utils import human_size, shorten_middle

RENDER_LIMIT = 100  # số dòng tối đa được vẽ; phần còn lại chỉ hiển thị số lượng


class FileListItem(ctk.CTkFrame):
    def __init__(self, master, path: str, is_dir: bool, size_text: str, on_remove: Callable[[str], None]):
        super().__init__(master, corner_radius=R_SM, fg_color=COLOR_SURFACE_MUTED)
        self.grid_columnconfigure(1, weight=1)
        p = Path(path)

        ctk.CTkLabel(
            self, text="", image=get_icon("folder" if is_dir else "file", 20, COLOR_TEXT_SECONDARY)
        ).grid(row=0, column=0, rowspan=2, padx=(SP12, SP8), pady=SP8)

        name = ctk.CTkLabel(
            self,
            text=shorten_middle(p.name or str(p), 52),
            font=FONT_BODY,
            text_color=COLOR_TEXT_PRIMARY,
            anchor="w",
            height=20,
        )
        name.grid(row=0, column=1, sticky="w", pady=(6, 0))
        loc = ctk.CTkLabel(
            self,
            text=shorten_middle(str(p.parent), 70),
            font=FONT_SMALL,
            text_color=COLOR_TEXT_MUTED,
            anchor="w",
            height=16,
        )
        loc.grid(row=1, column=1, sticky="w", pady=(0, 6))
        Tooltip(name, str(p))
        Tooltip(loc, str(p))

        self.size_lbl = ctk.CTkLabel(self, text=size_text, font=FONT_SMALL, text_color=COLOR_TEXT_SECONDARY)
        self.size_lbl.grid(row=0, column=2, rowspan=2, padx=SP8)

        IconButton(
            self, icon="close", tooltip="Xóa khỏi danh sách", size=30, icon_size=14,
            command=lambda: on_remove(path),
        ).grid(row=0, column=3, rowspan=2, padx=(0, SP8))


class FileList(ctk.CTkFrame):
    """Header (số mục • dung lượng • Xóa tất cả) + danh sách cuộn."""

    def __init__(self, master, on_remove: Callable[[str], None], on_clear: Callable[[], None]):
        super().__init__(master, **CARD_STYLE)
        self._on_remove = on_remove
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        head = ctk.CTkFrame(self, fg_color="transparent")
        head.grid(row=0, column=0, sticky="ew", padx=SP12, pady=(SP8, 0))
        head.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(head, text="File đã chọn", font=FONT_SECTION, text_color=COLOR_TEXT_PRIMARY).grid(
            row=0, column=0, sticky="w"
        )
        self.summary = ctk.CTkLabel(head, text="", font=FONT_SMALL, text_color=COLOR_TEXT_SECONDARY)
        self.summary.grid(row=0, column=1, padx=SP8)
        self.btn_clear = AppButton(
            head, text="Xóa tất cả", kind="ghost", height=28, font=FONT_SMALL, command=on_clear
        )
        self.btn_clear.grid(row=0, column=2)

        self.body = ctk.CTkScrollableFrame(self, fg_color="transparent", corner_radius=0)
        self.body.grid(row=1, column=0, sticky="nsew", padx=SP4, pady=(SP4, SP8))
        self.body.grid_columnconfigure(0, weight=1)

    def set_busy(self, busy: bool) -> None:
        self.btn_clear.configure(state="disabled" if busy else "normal")

    def render(self, items: list[dict], summary_text: str) -> None:
        """items: [{path, is_dir, size(int|None)}]; size None = đang tính."""
        self.summary.configure(text=summary_text)
        for child in self.body.winfo_children():
            child.destroy()
        for i, it in enumerate(items[:RENDER_LIMIT]):
            size = it.get("size")
            if it["is_dir"]:
                text = "Đang tính..." if size is None else human_size(size)
            else:
                text = human_size(size or 0)
            row = FileListItem(self.body, it["path"], it["is_dir"], text, self._on_remove)
            row.grid(row=i, column=0, sticky="ew", padx=SP4, pady=2)
        if len(items) > RENDER_LIMIT:
            ctk.CTkLabel(
                self.body,
                text=f"và {len(items) - RENDER_LIMIT} mục khác (vẫn được nén, chỉ không hiển thị để giữ app mượt)",
                font=FONT_SMALL,
                text_color=COLOR_TEXT_MUTED,
            ).grid(row=RENDER_LIMIT, column=0, pady=SP8)
