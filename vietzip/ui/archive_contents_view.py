"""Cửa sổ xem nội dung archive: tìm kiếm, lọc File/Thư mục, chọn nhiều mục để giải nén
riêng, xem trước nhanh (v2.1), hiển thị lười (lazy) cho archive lớn.
"""

from __future__ import annotations

from typing import Callable, Optional

import customtkinter as ctk

from vietzip.core.models import ArchiveEntry
from vietzip.ui.components import AppButton, EmptyState, Tooltip
from vietzip.ui.icons import get_icon
from vietzip.ui.theme import (
    CHECKBOX_STYLE,
    COLOR_BG,
    COLOR_BORDER,
    COLOR_SURFACE_MUTED,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    ENTRY_STYLE,
    FONT_HEADING,
    FONT_SMALL,
    R_MD,
    R_SM,
    SP4,
    SP8,
    SP12,
    SP16,
    SP20,
)
from vietzip.ui.widgets import setup_toplevel_window
from vietzip.utils.format_utils import format_count, human_size, shorten_middle

FILTERS = [("Tất cả", "all"), ("File", "file"), ("Thư mục", "dir")]
DISPLAY_STEP = 200  # số dòng vẽ mỗi lần, tránh lag với archive hàng chục nghìn mục

# Định dạng có thể xem trước ngay trong app (double-click), không cần giải nén ra đĩa.
PREVIEWABLE_TEXT_EXT = {
    ".txt", ".md", ".json", ".xml", ".csv", ".log", ".ini", ".cfg", ".yaml", ".yml",
    ".py", ".js", ".ts", ".html", ".css", ".c", ".cpp", ".h", ".java", ".sh", ".bat",
}
PREVIEWABLE_IMAGE_EXT = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"}
PREVIEW_MAX_BYTES = 5 * 1024 * 1024  # 5MB — vượt ngưỡng này thì không xem trước


def _dir_prefix(filename: str) -> str:
    return filename if filename.endswith("/") else filename + "/"


class ArchiveContentsWindow(ctk.CTkToplevel):
    def __init__(
        self,
        master,
        archive_name: str,
        entries: list[ArchiveEntry],
        zip_path: Optional[str] = None,
        password: Optional[str] = None,
        on_extract_selected: Optional[Callable[[list[str]], None]] = None,
    ):
        super().__init__(master, fg_color=COLOR_BG)
        self.title(f"Nội dung — {archive_name}")
        self.minsize(560, 420)
        setup_toplevel_window(self, master, 720, 600)
        self.entries = entries
        self.zip_path = zip_path
        self.password = password
        self.on_extract_selected = on_extract_selected
        self._by_name = {e.filename: e for e in entries}

        self.filtered: list[ArchiveEntry] = []
        self.selected: set[str] = set()
        self._filter = "all"
        self._limit = DISPLAY_STEP
        self._job: Optional[str] = None
        self._preview_win: Optional[ctk.CTkToplevel] = None

        self._build(archive_name)
        self.apply_filter()

    # ------------------------------------------------------------------ Dựng UI
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
        bar.grid_columnconfigure(0, weight=1)
        self.search = ctk.CTkEntry(bar, placeholder_text="Tìm file trong archive...", width=240, **ENTRY_STYLE)
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
        self.list.grid(row=2, column=0, sticky="nsew", padx=SP12, pady=(SP8, SP8))
        self.list.grid_columnconfigure(0, weight=1)

        # Chân cửa sổ: chọn tất cả + nút giải nén mục đã chọn (chỉ khi có callback)
        ctk.CTkFrame(self, height=1, fg_color=COLOR_BORDER).grid(row=3, column=0, sticky="new", padx=0)
        self.footer = ctk.CTkFrame(self, fg_color="transparent")
        self.footer.grid(row=4, column=0, sticky="ew", padx=SP20, pady=(SP12, SP16))
        self.footer.grid_columnconfigure(1, weight=1)

        self.btn_select_all = AppButton(
            self.footer, text="Chọn tất cả", kind="ghost", height=32, command=self._toggle_select_all
        )
        self.btn_select_all.grid(row=0, column=0, sticky="w")
        self.selected_lbl = ctk.CTkLabel(
            self.footer, text="", font=FONT_SMALL, text_color=COLOR_TEXT_SECONDARY, anchor="w"
        )
        self.selected_lbl.grid(row=0, column=1, sticky="w", padx=SP12)
        self.btn_extract_selected = AppButton(
            self.footer, text="Giải nén mục đã chọn", kind="primary", icon="open", height=36,
            command=self._extract_selected,
        )
        self.btn_extract_selected.grid(row=0, column=2, sticky="e")

        if self.on_extract_selected is None:
            self.footer.grid_remove()
        self._refresh_footer()

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

    # ------------------------------------------------------------------ Danh sách + chọn nhiều
    def _render(self):
        for w in self.list.winfo_children():
            w.destroy()
        if not self.filtered:
            EmptyState(self.list, title="Không tìm thấy mục nào", description="Thử từ khóa hoặc bộ lọc khác.",
                       icon="search", icon_size=32).grid(row=0, column=0, pady=SP16)
            self._refresh_footer()
            return
        limit = min(len(self.filtered), self._limit)
        for i in range(limit):
            self._build_row(i, self.filtered[i])
        if len(self.filtered) > limit:
            AppButton(self.list, text=f"Xem thêm (còn {format_count(len(self.filtered) - limit)} mục)",
                      kind="secondary", height=32, command=self._more).grid(row=limit, column=0, pady=SP8)
        self._refresh_footer()

    def _build_row(self, i: int, e: ArchiveEntry):
        row = ctk.CTkFrame(self.list, fg_color="transparent")
        row.grid(row=i, column=0, sticky="ew")
        row.grid_columnconfigure(2, weight=1)

        if self.on_extract_selected is not None:
            var = ctk.BooleanVar(value=e.filename in self.selected)
            ctk.CTkCheckBox(
                row, text="", variable=var, width=20, command=lambda ee=e, v=var: self._toggle(ee, v.get()),
                **CHECKBOX_STYLE,
            ).grid(row=0, column=0, padx=(SP4, SP4), pady=3)

        ctk.CTkLabel(row, text="", image=get_icon("folder" if e.is_dir else "file", 16, COLOR_TEXT_SECONDARY)).grid(
            row=0, column=1, padx=(0, SP8), pady=3
        )
        display_name = shorten_middle(e.filename.rstrip("/"), 70)
        can_preview = self._is_previewable(e)
        name = ctk.CTkLabel(
            row, text=display_name, font=FONT_SMALL,
            text_color=COLOR_TEXT_PRIMARY, anchor="w", cursor="hand2" if can_preview else "",
        )
        name.grid(row=0, column=2, sticky="w")
        Tooltip(name, e.filename + ("\n\nDouble-click để xem trước" if can_preview else ""))
        if can_preview:
            name.bind("<Double-Button-1>", lambda _ev, ee=e: self._open_preview(ee))

        if not e.is_dir:
            sz = human_size(e.file_size)
            if e.compress_size != e.file_size:
                sz += f"  ({human_size(e.compress_size)} nén)"
            ctk.CTkLabel(row, text=sz, font=FONT_SMALL, text_color=COLOR_TEXT_MUTED).grid(row=0, column=3, padx=SP8)

    def _more(self):
        self._limit += DISPLAY_STEP
        self._render()

    def _toggle(self, entry: ArchiveEntry, checked: bool):
        if checked:
            self.selected.add(entry.filename)
        else:
            self.selected.discard(entry.filename)
        self._refresh_footer()

    def _toggle_select_all(self):
        all_selected = bool(self.filtered) and all(e.filename in self.selected for e in self.filtered)
        if all_selected:
            for e in self.filtered:
                self.selected.discard(e.filename)
        else:
            for e in self.filtered:
                self.selected.add(e.filename)
        self._render()

    def _resolve_members(self) -> list[str]:
        """Mở rộng các mục đã chọn: chọn 1 thư mục nghĩa là chọn toàn bộ nội dung bên trong."""
        result: set[str] = set()
        for name in self.selected:
            entry = self._by_name.get(name)
            if entry is not None and entry.is_dir:
                prefix = _dir_prefix(name)
                for e in self.entries:
                    if e.filename == name or e.filename.startswith(prefix):
                        result.add(e.filename)
            else:
                result.add(name)
        return sorted(result)

    def _refresh_footer(self):
        if self.on_extract_selected is None:
            return
        n = len(self.selected)
        self.selected_lbl.configure(text=f"Đã chọn {format_count(n)} mục" if n else "Chưa chọn mục nào")
        self.btn_extract_selected.configure(text=f"Giải nén {n} mục đã chọn" if n else "Giải nén mục đã chọn")
        self.btn_extract_selected.configure(state="normal" if n else "disabled")
        if self.filtered:
            all_selected = all(e.filename in self.selected for e in self.filtered)
            self.btn_select_all.configure(text="Bỏ chọn tất cả" if all_selected else "Chọn tất cả")

    def _extract_selected(self):
        if not self.selected or self.on_extract_selected is None:
            return
        members = self._resolve_members()
        if not members:
            return
        self.on_extract_selected(members)
        self.destroy()

    # ------------------------------------------------------------------ Xem trước nhanh (double-click)
    def _is_previewable(self, e: ArchiveEntry) -> bool:
        if e.is_dir or self.zip_path is None or e.file_size > PREVIEW_MAX_BYTES:
            return False
        name = e.filename.lower()
        ext = "." + name.rsplit(".", 1)[-1] if "." in name else ""
        return ext in PREVIEWABLE_TEXT_EXT or ext in PREVIEWABLE_IMAGE_EXT

    def _open_preview(self, e: ArchiveEntry):
        if self._preview_win is not None and self._preview_win.winfo_exists():
            self._preview_win.destroy()
        name = e.filename.lower()
        ext = "." + name.rsplit(".", 1)[-1] if "." in name else ""
        try:
            data = self._read_entry_bytes(e.filename)
        except Exception as exc:  # noqa: BLE001 — xem trước là tiện ích phụ, lỗi không được làm crash app
            from vietzip.utils.error_utils import friendly_error
            self._show_preview_error(e.filename, friendly_error(str(exc), type(exc).__name__))
            return

        if ext in PREVIEWABLE_IMAGE_EXT:
            self._show_image_preview(e.filename, data)
        else:
            self._show_text_preview(e.filename, data)

    def _read_entry_bytes(self, filename: str) -> bytes:
        import zipfile as _zipfile
        try:
            import pyzipper
            opener = pyzipper.AESZipFile
        except ImportError:
            opener = _zipfile.ZipFile
        with opener(self.zip_path, "r") as zf:
            if self.password:
                zf.setpassword(self.password.encode("utf-8"))
            return zf.read(filename)

    def _preview_shell(self, title: str, width: int = 640, height: int = 480) -> ctk.CTkToplevel:
        win = ctk.CTkToplevel(self, fg_color=COLOR_BG)
        win.title(f"Xem trước — {title}")
        setup_toplevel_window(win, self, width, height)
        self._preview_win = win
        return win

    def _show_preview_error(self, filename: str, message: str):
        win = self._preview_shell(shorten_middle(filename, 50), 420, 200)
        EmptyState(win, title="Không xem trước được", description=message, icon="warn").pack(
            fill="both", expand=True
        )

    def _show_text_preview(self, filename: str, data: bytes):
        win = self._preview_shell(shorten_middle(filename, 50))
        win.grid_columnconfigure(0, weight=1)
        win.grid_rowconfigure(0, weight=1)
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            text = data.decode("utf-8", errors="replace")
        box = ctk.CTkTextbox(win, wrap="none", font=("Consolas", 12))
        box.grid(row=0, column=0, sticky="nsew", padx=SP12, pady=SP12)
        box.insert("1.0", text)
        box.configure(state="disabled")

    def _show_image_preview(self, filename: str, data: bytes):
        import io
        from PIL import Image

        win = self._preview_shell(shorten_middle(filename, 50))
        try:
            with Image.open(io.BytesIO(data)) as im:
                im = im.convert("RGBA")
                im.thumbnail((760, 760))
                photo = ctk.CTkImage(light_image=im, dark_image=im, size=im.size)
        except Exception:  # noqa: BLE001 — dữ liệu ảnh lỗi/không hỗ trợ định dạng
            self._show_preview_error(filename, "Không đọc được dữ liệu ảnh này.")
            return
        self._img_ref = photo  # giữ tham chiếu để tránh bị garbage-collect
        ctk.CTkLabel(win, text="", image=photo).pack(expand=True, padx=SP12, pady=SP12)
