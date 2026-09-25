"""Cửa sổ xem nội dung archive: tìm kiếm, lọc File/Thư mục, hiển thị lười (lazy) cho archive lớn."""

from __future__ import annotations

from typing import Optional

import customtkinter as ctk

from vietzip.core.models import ArchiveEntry
from vietzip.ui.components import AppButton, EmptyState, Tooltip
from vietzip.ui.icons import get_icon
from vietzip.ui.theme import (
    COLOR_BG,
    COLOR_SURFACE_MUTED,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    ENTRY_STYLE,
    FONT_HEADING,
    FONT_SMALL,
    R_MD,
    R_SM,
    SP8,
    SP12,
    SP16,
    SP20,
)
from vietzip.ui.widgets import setup_toplevel_window
from vietzip.utils.format_utils import format_count, human_size, shorten_middle

FILTERS = [("Tất cả", "all"), ("File", "file"), ("Thư mục", "dir")]
DISPLAY_STEP = 200  # số dòng vẽ mỗi lần, tránh lag với archive hàng chục nghìn mục


class ArchiveContentsWindow(ctk.CTkToplevel):
    def __init__(self, master, archive_name: str, entries: list[ArchiveEntry]):
        super().__init__(master, fg_color=COLOR_BG)
        self.title(f"Nội dung — {archive_name}")
        self.minsize(560, 380)
        setup_toplevel_window(self, master, 720, 560)
        self.entries = entries
        self.filtered: list[ArchiveEntry] = []
        self._filter = "all"
        self._limit = DISPLAY_STEP
        self._job: Optional[str] = None
        self._build(archive_name)
        self.apply_filter()

    def _build(self, name: str):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        ctk.CTkLabel(
            self, text=shorten_middle(name, 60), font=FONT_HEADING, text_color=COLOR_TEXT_PRIMARY, anchor="w"
        ).grid(row=0, column=0, sticky="w", padx=SP20, pady=(SP16, 0))
        self.count_lbl = ctk.CTkLabel(self, text="", font=FONT_SMALL, text_color=COLOR_TEXT_SECONDARY, anchor="w")
        self.count_lbl.grid(row=1, column=0, sticky="w", padx=SP20)

        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.grid(row=1, column=0, sticky="e", padx=SP20, pady=(SP12, 0))
        # (hàng 1 dùng chung: nhãn đếm bên trái, ô tìm kiếm bên phải)
        bar.grid_columnconfigure(0, weight=1)
        self.search = ctk.CTkEntry(bar, placeholder_text="Tìm file trong archive...", width=260, **ENTRY_STYLE)
        self.search.grid(row=0, column=0, padx=(0, SP8))
        self.search.bind("<KeyRelease>", lambda e: self._debounce(), add="+")
        seg = ctk.CTkFrame(bar, corner_radius=R_MD, fg_color=COLOR_SURFACE_MUTED)
        seg.grid(row=0, column=1)
        self._btns: dict[str, AppButton] = {}
        for i, (label, key) in enumerate(FILTERS):
            b = AppButton(seg, text=label, kind="ghost", height=30, width=72, font=FONT_SMALL,
                          corner_radius=R_SM, command=lambda k=key: self._set_filter(k))
            b.grid(row=0, column=i, padx=2, pady=2)
            self._btns[key] = b
        self._paint()

        self.list = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.list.grid(row=2, column=0, sticky="nsew", padx=SP12, pady=(SP8, SP12))
        self.list.grid_columnconfigure(0, weight=1)

    def _paint(self):
        for key, b in self._btns.items():
            b.set_kind("primary" if key == self._filter else "ghost")

    def _set_filter(self, key: str):
        self._filter = key
        self._paint()
        self._limit = DISPLAY_STEP
        self.apply_filter()

    def _debounce(self):
        if self._job:
            self.after_cancel(self._job)
        self._job = self.after(180, self.apply_filter)

    def apply_filter(self):
        self._job = None
        q = self.search.get().strip().lower()
        out = []
        for e in self.entries:
            if self._filter == "file" and e.is_dir:
                continue
            if self._filter == "dir" and not e.is_dir:
                continue
            if q and q not in e.filename.lower():
                continue
            out.append(e)
        self.filtered = out
        self.count_lbl.configure(text=f"{format_count(len(out))} / {format_count(len(self.entries))} mục")
        self._render()

    def _render(self):
        for w in self.list.winfo_children():
            w.destroy()
        if not self.filtered:
            EmptyState(self.list, title="Không tìm thấy mục nào", description="Thử từ khóa hoặc bộ lọc khác.",
                       icon="search", icon_size=32).grid(row=0, column=0, pady=SP16)
            return
        limit = min(len(self.filtered), self._limit)
        for i in range(limit):
            e = self.filtered[i]
            row = ctk.CTkFrame(self.list, fg_color="transparent")
            row.grid(row=i, column=0, sticky="ew")
            row.grid_columnconfigure(1, weight=1)
            ctk.CTkLabel(row, text="", image=get_icon("folder" if e.is_dir else "file", 16, COLOR_TEXT_SECONDARY)).grid(
                row=0, column=0, padx=(SP8, SP8), pady=3
            )
            name = ctk.CTkLabel(row, text=shorten_middle(e.filename.rstrip("/"), 80), font=FONT_SMALL,
                                text_color=COLOR_TEXT_PRIMARY, anchor="w")
            name.grid(row=0, column=1, sticky="w")
            Tooltip(name, e.filename)
            if not e.is_dir:
                sz = human_size(e.file_size)
                if e.compress_size != e.file_size:
                    sz += f"  ({human_size(e.compress_size)} nén)"
                ctk.CTkLabel(row, text=sz, font=FONT_SMALL, text_color=COLOR_TEXT_MUTED).grid(row=0, column=2, padx=SP8)
        if len(self.filtered) > limit:
            AppButton(self.list, text=f"Xem thêm (còn {format_count(len(self.filtered) - limit)} mục)",
                      kind="secondary", height=32, command=self._more).grid(row=limit, column=0, pady=SP8)

    def _more(self):
        self._limit += DISPLAY_STEP
        self._render()
