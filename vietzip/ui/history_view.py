"""Cửa sổ Lịch sử: tìm kiếm, lọc, nhóm theo ngày, thẻ gọn."""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from tkinter import messagebox

import customtkinter as ctk

from vietzip.services.history_service import history_service
from vietzip.ui.components import AppButton, EmptyState, IconButton, StatusBadge
from vietzip.ui.icons import get_icon
from vietzip.ui.theme import (
    COLOR_BG,
    COLOR_SURFACE,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    ENTRY_STYLE,
    FONT_BODY,
    FONT_HEADING,
    FONT_SECTION,
    FONT_SMALL,
    OPTION_STYLE,
    R_MD,
    SP4,
    SP8,
    SP12,
    SP16,
    SP20,
)
from vietzip.ui.widgets import setup_toplevel_window
from vietzip.utils.file_utils import open_file, open_in_explorer
from vietzip.utils.format_utils import human_size, shorten_middle

FILTERS = {"Tất cả": None, "Nén": "compress", "Giải nén": "extract"}
PAGE = 100


def _parse_ts(ts: str) -> datetime:
    try:
        return datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError):
        return datetime.min


def _day_label(dt: datetime) -> str:
    today = datetime.now().date()
    if dt.date() == today:
        return "Hôm nay"
    if dt.date() == today - timedelta(days=1):
        return "Hôm qua"
    return dt.strftime("%d/%m/%Y")


class HistoryWindow(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master, fg_color=COLOR_BG)
        self.title("Lịch sử — VietZIP")
        self.minsize(640, 420)
        self._limit = PAGE
        setup_toplevel_window(self, master, 760, 580)
        self._build()
        self._render()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        top = ctk.CTkFrame(self, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", padx=SP20, pady=(SP16, SP8))
        top.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(top, text="Lịch sử", font=FONT_HEADING, text_color=COLOR_TEXT_PRIMARY).grid(
            row=0, column=0, sticky="w", columnspan=3
        )
        self.search = ctk.CTkEntry(top, placeholder_text="Tìm kiếm...", **ENTRY_STYLE)
        self.search.grid(row=1, column=0, columnspan=2, sticky="ew", padx=(0, SP8), pady=(SP8, 0))
        self.search.bind("<KeyRelease>", lambda e: self._reset_and_render(), add="+")
        self.filter = ctk.CTkOptionMenu(
            top, values=list(FILTERS), width=130, command=lambda v: self._reset_and_render(), **OPTION_STYLE
        )
        self.filter.set("Tất cả")
        self.filter.grid(row=1, column=2, pady=(SP8, 0), padx=(0, SP8))
        AppButton(top, text="Xóa lịch sử", kind="secondary", icon="trash", command=self._clear_all).grid(
            row=1, column=3, pady=(SP8, 0)
        )

        self.body = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.body.grid(row=1, column=0, sticky="nsew", padx=SP12, pady=(0, SP12))
        self.body.grid_columnconfigure(0, weight=1)

    def _reset_and_render(self):
        self._limit = PAGE
        self._render()

    def _filtered(self) -> list[dict]:
        q = self.search.get().strip().lower()
        op = FILTERS.get(self.filter.get())
        out = []
        for r in history_service.get_records():
            if op and r.get("operation") != op:
                continue
            hay = f"{r.get('input_summary', '')} {Path(r.get('output_path') or '').name}".lower()
            if q and q not in hay:
                continue
            out.append(r)
        return out

    def _render(self):
        for w in self.body.winfo_children():
            w.destroy()
        records = self._filtered()
        if not records:
            has_any = bool(history_service.get_records())
            EmptyState(
                self.body,
                title="Không có kết quả" if has_any else "Chưa có lịch sử",
                description="Thử từ khóa hoặc bộ lọc khác." if has_any
                else "Các lần nén và giải nén của bạn sẽ hiện ở đây.",
                icon="search" if has_any else "clock",
            ).grid(row=0, column=0, pady=48)
            return

        row = 0
        current_day = None
        for rec in records[: self._limit]:
            dt = _parse_ts(rec.get("timestamp", ""))
            day = _day_label(dt)
            if day != current_day:
                current_day = day
                ctk.CTkLabel(
                    self.body, text=day, font=FONT_SECTION, text_color=COLOR_TEXT_SECONDARY, anchor="w"
                ).grid(row=row, column=0, sticky="w", padx=SP8, pady=(SP12, SP4))
                row += 1
            self._card(rec, dt).grid(row=row, column=0, sticky="ew", padx=SP4, pady=3)
            row += 1
        if len(records) > self._limit:
            AppButton(
                self.body, text=f"Xem thêm ({len(records) - self._limit} mục)", kind="secondary",
                command=self._more,
            ).grid(row=row, column=0, pady=SP12)

    def _more(self):
        self._limit += PAGE
        self._render()

    def _card(self, rec: dict, dt: datetime) -> ctk.CTkFrame:
        card = ctk.CTkFrame(self.body, corner_radius=R_MD, fg_color=COLOR_SURFACE)
        card.grid_columnconfigure(1, weight=1)
        is_comp = rec.get("operation") == "compress"
        out = rec.get("output_path") or ""
        name = Path(out).name if out else (rec.get("input_summary") or "—")
        status = rec.get("status", "success")
        exists = bool(out) and Path(out).exists()

        ctk.CTkLabel(
            card, text="", image=get_icon("archive" if is_comp else "open", 22, COLOR_TEXT_SECONDARY)
        ).grid(row=0, column=0, rowspan=3, padx=(SP12, SP8), pady=SP12, sticky="n")
        ctk.CTkLabel(
            card, text=shorten_middle(name, 46), font=FONT_BODY, text_color=COLOR_TEXT_PRIMARY, anchor="w"
        ).grid(row=0, column=1, sticky="w", pady=(SP12, 0))
        StatusBadge(card, status).grid(row=0, column=2, padx=SP12, pady=(SP12, 0), sticky="e")

        orig, final = rec.get("original_size", 0), rec.get("final_size", 0)
        parts = ["Nén" if is_comp else "Giải nén", f"{rec.get('file_count', 0)} mục"]
        if is_comp and orig > 0 and status == "success":
            parts.append(f"{human_size(orig)} → {human_size(final)}")
        parts.append(f"{rec.get('elapsed_seconds', 0)}s")
        ctk.CTkLabel(card, text=" • ".join(parts), font=FONT_SMALL, text_color=COLOR_TEXT_SECONDARY, anchor="w").grid(
            row=1, column=1, columnspan=2, sticky="w"
        )
        time_txt = dt.strftime("%H:%M") if dt != datetime.min else ""
        if status == "error" and rec.get("error_message"):
            time_txt += f"  ·  {shorten_middle(rec['error_message'], 70)}"
        elif out and not exists and status == "success":
            time_txt += "  ·  File không còn tồn tại"
        ctk.CTkLabel(card, text=time_txt, font=FONT_SMALL, text_color=COLOR_TEXT_MUTED, anchor="w").grid(
            row=2, column=1, columnspan=2, sticky="w", pady=(0, SP12)
        )

        acts = ctk.CTkFrame(card, fg_color="transparent")
        acts.grid(row=0, column=3, rowspan=3, padx=(0, SP12))
        if exists:
            if Path(out).is_file():
                AppButton(acts, text="Mở", kind="secondary", height=30, width=56, font=FONT_SMALL,
                          command=lambda p=out: open_file(p)).pack(side="left", padx=SP4)
            AppButton(acts, text="Thư mục", kind="secondary", height=30, width=72, font=FONT_SMALL,
                      command=lambda p=out: open_in_explorer(p)).pack(side="left", padx=SP4)
        IconButton(acts, icon="trash", tooltip="Xóa bản ghi này", size=30, icon_size=14,
                   command=lambda r=rec.get("id"): self._remove(r)).pack(side="left", padx=SP4)
        return card

    def _remove(self, record_id):
        history_service.remove_record(record_id)
        self._render()

    def _clear_all(self):
        if messagebox.askyesno("Xóa lịch sử", "Xóa toàn bộ lịch sử? Thao tác này không thể hoàn tác.",
                               icon="warning", parent=self):
            history_service.clear()
            self._render()
