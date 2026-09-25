"""FileList + FileListItem: danh sách nguồn cần nén.

v2.1: hỗ trợ chọn nhiều dòng (click / Ctrl+click / Shift+click) để xóa hàng loạt,
ngoài việc xóa từng dòng bằng nút "x" hoặc xóa tất cả như trước.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Optional

import customtkinter as ctk

from vietzip.ui.components.icon_button import AppButton, IconButton
from vietzip.ui.components.tooltip import Tooltip
from vietzip.ui.icons import get_icon
from vietzip.ui.theme import (
    CARD_STYLE,
    COLOR_PRIMARY_SOFT,
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

# Bitmask trạng thái phím bổ trợ trong sự kiện Tk — giống nhau trên Windows/Linux/macOS.
_SHIFT_MASK = 0x0001
_CTRL_MASK = 0x0004


class FileListItem(ctk.CTkFrame):
    def __init__(
        self,
        master,
        path: str,
        is_dir: bool,
        size_text: str,
        on_remove: Callable[[str], None],
        on_click: Callable[[str, object], None],  # object = tkinter.Event; tránh import tkinter chỉ để gợi ý kiểu
    ):
        super().__init__(master, corner_radius=R_SM, fg_color=COLOR_SURFACE_MUTED)
        self.path = path
        self.grid_columnconfigure(1, weight=1)
        p = Path(path)

        icon_lbl = ctk.CTkLabel(
            self, text="", image=get_icon("folder" if is_dir else "file", 20, COLOR_TEXT_SECONDARY)
        )
        icon_lbl.grid(row=0, column=0, rowspan=2, padx=(SP12, SP8), pady=SP8)

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

        # Toàn bộ phần thân dòng (trừ nút "x") có thể click để chọn/bỏ chọn.
        for w in (self, icon_lbl, name, loc, self.size_lbl):
            w.bind("<Button-1>", lambda e, pth=path: on_click(pth, e), add="+")

    def set_selected(self, selected: bool) -> None:
        self.configure(fg_color=COLOR_PRIMARY_SOFT if selected else COLOR_SURFACE_MUTED)


class FileList(ctk.CTkFrame):
    """Header (số mục • dung lượng • xóa) + danh sách cuộn có thể chọn nhiều dòng."""

    def __init__(
        self,
        master,
        on_remove: Callable[[str], None],
        on_clear: Callable[[], None],
        on_remove_many: Optional[Callable[[list[str]], None]] = None,
    ):
        super().__init__(master, **CARD_STYLE)
        self._on_remove = on_remove
        self._on_remove_many = on_remove_many
        self._order: list[str] = []  # thứ tự path hiện có, dùng để tính vùng chọn Shift
        self._rows: dict[str, FileListItem] = {}
        self.selected: set[str] = set()
        self._anchor: Optional[str] = None

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
        self.btn_remove_selected = AppButton(
            head, text="", kind="secondary", height=28, font=FONT_SMALL, command=self._remove_selected,
        )
        self.btn_remove_selected.grid(row=0, column=2, padx=(0, SP8))
        self.btn_remove_selected.grid_remove()
        self.btn_clear = AppButton(
            head, text="Xóa tất cả", kind="ghost", height=28, font=FONT_SMALL, command=on_clear
        )
        self.btn_clear.grid(row=0, column=3)

        self.body = ctk.CTkScrollableFrame(self, fg_color="transparent", corner_radius=0)
        self.body.grid(row=1, column=0, sticky="nsew", padx=SP4, pady=(SP4, SP8))
        self.body.grid_columnconfigure(0, weight=1)
        # Click vào khoảng trống bên dưới danh sách để bỏ chọn hết — tiện khi lỡ chọn nhầm.
        self.body.bind("<Button-1>", lambda e: self._clear_selection(), add="+")

    def set_busy(self, busy: bool) -> None:
        state = "disabled" if busy else "normal"
        self.btn_clear.configure(state=state)
        self.btn_remove_selected.configure(state=state)

    def render(self, items: list[dict], summary_text: str) -> None:
        """items: [{path, is_dir, size(int|None)}]; size None = đang tính."""
        self.summary.configure(text=summary_text)
        current_paths = {it["path"] for it in items}
        self.selected &= current_paths  # bỏ chọn những mục đã bị xóa khỏi danh sách nguồn
        if self._anchor not in current_paths:
            self._anchor = None
        self._order = [it["path"] for it in items]

        for child in self.body.winfo_children():
            child.destroy()
        self._rows = {}
        for i, it in enumerate(items[:RENDER_LIMIT]):
            size = it.get("size")
            if it["is_dir"]:
                text = "Đang tính..." if size is None else human_size(size)
            else:
                text = human_size(size or 0)
            row = FileListItem(self.body, it["path"], it["is_dir"], text, self._on_remove, self._on_row_click)
            row.grid(row=i, column=0, sticky="ew", padx=SP4, pady=2)
            row.set_selected(it["path"] in self.selected)
            self._rows[it["path"]] = row
        if len(items) > RENDER_LIMIT:
            ctk.CTkLabel(
                self.body,
                text=f"và {len(items) - RENDER_LIMIT} mục khác (vẫn được nén, chỉ không hiển thị để giữ app mượt)",
                font=FONT_SMALL,
                text_color=COLOR_TEXT_MUTED,
            ).grid(row=RENDER_LIMIT, column=0, pady=SP8)
        self._update_header()

    # ------------------------------------------------------------------ Chọn nhiều dòng
    def _on_row_click(self, path: str, event) -> None:
        shift = bool(event.state & _SHIFT_MASK)
        ctrl = bool(event.state & _CTRL_MASK)

        if shift and self._anchor is not None and self._anchor in self._order and path in self._order:
            a, b = sorted((self._order.index(self._anchor), self._order.index(path)))
            self.selected = set(self._order[a : b + 1])
        elif ctrl:
            if path in self.selected:
                self.selected.discard(path)
            else:
                self.selected.add(path)
            self._anchor = path
        else:
            self.selected = {path}
            self._anchor = path

        for p, row in self._rows.items():
            row.set_selected(p in self.selected)
        self._update_header()

    def _clear_selection(self) -> None:
        if not self.selected:
            return
        self.selected.clear()
        for row in self._rows.values():
            row.set_selected(False)
        self._update_header()

    def _remove_selected(self) -> None:
        if not self.selected or self._on_remove_many is None:
            return
        self._on_remove_many(sorted(self.selected))

    def _update_header(self) -> None:
        n = len(self.selected)
        if n and self._on_remove_many is not None:
            self.btn_remove_selected.configure(text=f"Xóa {n} mục đã chọn")
            self.btn_remove_selected.grid()
        else:
            self.btn_remove_selected.grid_remove()
