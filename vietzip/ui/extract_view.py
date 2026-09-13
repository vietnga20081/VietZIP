"""Extraction tab view."""

from __future__ import annotations

import os
from pathlib import Path
from tkinter import filedialog, messagebox
from typing import Callable, Optional
import customtkinter as ctk

from vietzip.core.archive_info import get_archive_metadata, list_archive_entries
from vietzip.core.models import ArchiveEntry, ArchiveMetadata
from vietzip.services.recent_service import recent_service
from vietzip.services.settings_service import settings_service
from vietzip.ui.theme import (
    COLOR_CARD,
    COLOR_CARD_ALT,
    COLOR_BORDER,
    COLOR_PRIMARY,
    COLOR_BTN_OUTLINE_TEXT,
    COLOR_SEGMENT_TEXT,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    BTN_SECONDARY_STYLE,
    FONT_MONO,
    FONT_REGULAR,
    FONT_SECTION,
    FONT_SMALL,
)
from vietzip.utils.format_utils import human_size


class ExtractView(ctk.CTkFrame):
    """Giao diện tab Giải nén file ZIP."""

    def __init__(
        self,
        master,
        on_start_extract: Callable[[str, str, Optional[str]], None],
        **kwargs,
    ):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.on_start_extract = on_start_extract

        self.current_zip_path: Optional[str] = None
        self.archive_metadata: Optional[ArchiveMetadata] = None
        self.all_entries: list[ArchiveEntry] = []
        self.filtered_entries: list[ArchiveEntry] = []
        self._display_limit = 300
        self._is_busy = False

        self._build_layout()

    def _build_layout(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # 1. Chọn file ZIP & Nơi giải nén
        pick_section = ctk.CTkFrame(
            self,
            corner_radius=12,
            border_width=1,
            border_color=COLOR_BORDER,
            fg_color=COLOR_CARD,
        )
        pick_section.grid(row=0, column=0, sticky="ew", pady=(8, 6), padx=2)
        pick_section.grid_columnconfigure(1, weight=1)

        # Row 1: Pick ZIP
        ctk.CTkLabel(
            pick_section, text="📦 File ZIP:", font=FONT_REGULAR, text_color=COLOR_TEXT_PRIMARY, width=90, anchor="w"
        ).grid(row=0, column=0, padx=(12, 6), pady=(10, 4), sticky="w")

        self.zip_path_entry = ctk.CTkEntry(
            pick_section,
            placeholder_text="Chọn file ZIP hoặc kéo thả vào đây...",
            text_color=COLOR_TEXT_PRIMARY,
        )
        self.zip_path_entry.grid(row=0, column=1, sticky="ew", padx=6, pady=(10, 4))

        ctk.CTkButton(
            pick_section,
            text="Chọn ZIP",
            width=100,
            command=self._choose_zip_file,
        ).grid(row=0, column=2, padx=(6, 12), pady=(10, 4))

        # Row 2: Pick Destination
        ctk.CTkLabel(
            pick_section, text="📂 Nơi giải nén:", font=FONT_REGULAR, text_color=COLOR_TEXT_PRIMARY, width=90, anchor="w"
        ).grid(row=1, column=0, padx=(12, 6), pady=(4, 6), sticky="w")

        self.dest_dir_entry = ctk.CTkEntry(
            pick_section,
            placeholder_text="Thư mục sẽ giải nén các file ra...",
            text_color=COLOR_TEXT_PRIMARY,
        )
        self.dest_dir_entry.grid(row=1, column=1, sticky="ew", padx=6, pady=(4, 6))

        ctk.CTkButton(
            pick_section,
            text="Chọn thư mục",
            width=100,
            command=self._choose_dest_dir,
        ).grid(row=1, column=2, padx=(6, 12), pady=(4, 6))

        # Row 3: Subfolder option & Password
        opt_row = ctk.CTkFrame(pick_section, fg_color="transparent")
        opt_row.grid(row=2, column=0, columnspan=3, sticky="ew", padx=12, pady=(0, 10))

        self.create_subfolder_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            opt_row,
            text="Tạo thư mục con theo tên file ZIP",
            variable=self.create_subfolder_var,
            font=FONT_SMALL,
            text_color=COLOR_TEXT_PRIMARY,
            command=self._on_subfolder_toggle,
        ).pack(side="left")

        self.pwd_entry = ctk.CTkEntry(
            opt_row,
            placeholder_text="Mật khẩu (nếu có)",
            show="•",
            width=160,
            text_color=COLOR_TEXT_PRIMARY,
        )
        self.pwd_entry.pack(side="right", padx=(8, 0))

        self.show_pwd_var = ctk.BooleanVar(value=False)
        self.show_pwd_chk = ctk.CTkCheckBox(
            opt_row,
            text="Hiện",
            variable=self.show_pwd_var,
            font=FONT_SMALL,
            text_color=COLOR_TEXT_PRIMARY,
            command=self._toggle_show_pwd,
        ).pack(side="right")

        ctk.CTkLabel(
            opt_row,
            text="🔐 Mật khẩu:",
            font=FONT_SMALL,
            text_color=COLOR_TEXT_PRIMARY,
        ).pack(side="right", padx=(10, 4))

        # 2. Metadata Bar
        self.meta_card = ctk.CTkFrame(
            self,
            corner_radius=8,
            fg_color=COLOR_CARD_ALT,
            border_width=1,
            border_color=COLOR_BORDER,
        )
        self.meta_card.grid(row=1, column=0, sticky="ew", pady=(0, 6), padx=2)
        self.meta_label = ctk.CTkLabel(
            self.meta_card,
            text="Chưa có file ZIP nào được chọn.",
            font=FONT_SMALL,
            text_color=COLOR_TEXT_PRIMARY,
            anchor="w",
        )
        self.meta_label.pack(side="left", padx=12, pady=6)

        # 3. Preview Container (Search, Filter, List)
        preview_frame = ctk.CTkFrame(
            self,
            corner_radius=12,
            border_width=1,
            border_color=COLOR_BORDER,
            fg_color=COLOR_CARD,
        )
        preview_frame.grid(row=2, column=0, sticky="nsew", pady=(0, 6), padx=2)
        preview_frame.grid_columnconfigure(0, weight=1)
        preview_frame.grid_rowconfigure(1, weight=1)

        # Search and Filter Toolbar
        search_bar = ctk.CTkFrame(preview_frame, fg_color="transparent")
        search_bar.grid(row=0, column=0, sticky="ew", padx=10, pady=(8, 6))
        search_bar.grid_columnconfigure(0, weight=1)

        self.search_entry = ctk.CTkEntry(
            search_bar,
            placeholder_text="🔎 Tìm kiếm file trong archive...",
            height=30,
            text_color=COLOR_TEXT_PRIMARY,
        )
        self.search_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.search_entry.bind("<KeyRelease>", lambda e: self._on_filter_changed())

        self.filter_seg = ctk.CTkSegmentedButton(
            search_bar,
            values=["Tất cả", "Chỉ file", "Chỉ thư mục"],
            text_color=COLOR_SEGMENT_TEXT,
            unselected_color=("#E2E8F0", "gray29"),
            unselected_hover_color=("#CBD5E1", "gray41"),
            command=lambda v: self._on_filter_changed(),
        )
        self.filter_seg.set("Tất cả")
        self.filter_seg.grid(row=0, column=1)

        # Content List Scrollable
        self.contents_list = ctk.CTkScrollableFrame(
            preview_frame,
            fg_color="transparent",
        )
        self.contents_list.grid(row=1, column=0, sticky="nsew", padx=4, pady=(0, 4))
        self.contents_list.grid_columnconfigure(0, weight=1)

        self._render_empty_preview()

        # 4. Big Extract Button
        self.btn_extract = ctk.CTkButton(
            self,
            text="✨ Giải nén ngay!",
            height=46,
            font=("Segoe UI", 15, "bold"),
            command=self._on_click_extract,
        )
        self.btn_extract.grid(row=3, column=0, sticky="ew", pady=(2, 8))

    def _toggle_show_pwd(self):
        if self.show_pwd_var.get():
            self.pwd_entry.configure(show="")
        else:
            self.pwd_entry.configure(show="•")

    def _render_empty_preview(self):
        for child in self.contents_list.winfo_children():
            child.destroy()

        empty_box = ctk.CTkFrame(self.contents_list, fg_color="transparent")
        empty_box.pack(pady=40)

        ctk.CTkLabel(
            empty_box,
            text="📂",
            font=("Segoe UI Emoji", 40),
        ).pack(pady=(0, 4))

        ctk.CTkLabel(
            empty_box,
            text="Chưa có nội dung xem trước",
            font=FONT_SECTION,
            text_color=COLOR_TEXT_PRIMARY,
        ).pack()

        ctk.CTkLabel(
            empty_box,
            text="Hãy chọn file ZIP để xem danh sách các mục bên trong",
            font=FONT_REGULAR,
            text_color=COLOR_TEXT_SECONDARY,
        ).pack(pady=(4, 0))

    def load_zip(self, file_path: str):
        """Nạp file ZIP và hiển thị metadata cùng nội dung xem trước."""
        p = Path(file_path).resolve()
        if not p.exists() or not p.is_file():
            messagebox.showerror("VietZIP", f"File không tồn tại: {file_path}", parent=self.winfo_toplevel())
            return

        self.current_zip_path = str(p)
        self.zip_path_entry.delete(0, "end")
        self.zip_path_entry.insert(0, str(p))

        # Lưu vào danh sách gần đây
        recent_service.add(str(p))

        # Tự động gợi ý thư mục giải nén
        self._update_suggested_dest_dir(p)

        try:
            self.archive_metadata = get_archive_metadata(p)
            self.all_entries = list_archive_entries(p)
        except Exception as exc:
            messagebox.showerror("VietZIP", f"Không thể đọc file ZIP:\n{exc}", parent=self.winfo_toplevel())
            self.meta_label.configure(text=f"⚠️ Lỗi đọc file ZIP: {exc}")
            return

        # Cập nhật metadata bar
        enc_badge = " • 🔐 Có mật khẩu" if self.archive_metadata.is_encrypted else ""
        self.meta_label.configure(
            text=(
                f"📦 {p.name} • {human_size(self.archive_metadata.file_size)} "
                f"({self.archive_metadata.total_entries} mục, uncompressed: "
                f"{human_size(self.archive_metadata.uncompressed_size)}, "
                f"tỷ lệ: {self.archive_metadata.ratio_percent:.1f}%){enc_badge}"
            )
        )

        # Cảnh báo Zip bomb nếu có
        if self.archive_metadata.has_zip_bomb_risk:
            messagebox.showwarning(
                "Cảnh báo Archive",
                self.archive_metadata.zip_bomb_warning
                or "Archive có tỷ lệ nén bất thường, hãy cẩn thận khi giải nén!",
                parent=self.winfo_toplevel(),
            )

        self._on_filter_changed()

    def _update_suggested_dest_dir(self, zip_path: Path):
        parent_dir = zip_path.parent
        if self.create_subfolder_var.get():
            target = parent_dir / zip_path.stem
        else:
            target = parent_dir
        self.dest_dir_entry.delete(0, "end")
        self.dest_dir_entry.insert(0, str(target))

    def _on_subfolder_toggle(self):
        if self.current_zip_path:
            self._update_suggested_dest_dir(Path(self.current_zip_path))

    def _choose_zip_file(self):
        path = filedialog.askopenfilename(
            title="Chọn file ZIP cần giải nén",
            filetypes=[("ZIP Archive", "*.zip"), ("All Files", "*.*")],
            parent=self.winfo_toplevel(),
        )
        if path:
            self.load_zip(path)

    def _choose_dest_dir(self):
        dir_path = filedialog.askdirectory(title="Chọn thư mục giải nén", parent=self.winfo_toplevel())
        if dir_path:
            self.dest_dir_entry.delete(0, "end")
            self.dest_dir_entry.insert(0, dir_path)

    def _on_filter_changed(self):
        """Lọc danh sách file theo từ khóa tìm kiếm và loại mục."""
        if not self.all_entries:
            self._render_empty_preview()
            return

        query = self.search_entry.get().strip().lower()
        filter_mode = self.filter_seg.get()

        matched: list[ArchiveEntry] = []
        for entry in self.all_entries:
            if filter_mode == "Chỉ file" and entry.is_dir:
                continue
            if filter_mode == "Chỉ thư mục" and not entry.is_dir:
                continue
            if query and query not in entry.filename.lower():
                continue
            matched.append(entry)

        self.filtered_entries = matched
        self._render_entries()

    def _render_entries(self):
        for child in self.contents_list.winfo_children():
            child.destroy()

        if not self.filtered_entries:
            ctk.CTkLabel(
                self.contents_list,
                text="Không tìm thấy mục nào phù hợp.",
                font=FONT_SMALL,
                text_color=COLOR_TEXT_SECONDARY,
            ).pack(pady=20)
            return

        # Hiển thị tối đa _display_limit mục để giữ UI luôn mượt mà
        limit = min(len(self.filtered_entries), self._display_limit)
        for i in range(limit):
            entry = self.filtered_entries[i]
            icon = "📁" if entry.is_dir else "📄"

            row = ctk.CTkFrame(
                self.contents_list,
                corner_radius=6,
                fg_color=("gray95", "gray18") if i % 2 == 0 else "transparent",
            )
            row.pack(fill="x", pady=1, padx=2)
            row.grid_columnconfigure(1, weight=1)

            ctk.CTkLabel(row, text=icon, font=("Segoe UI Emoji", 14)).grid(
                row=0, column=0, padx=(8, 4), pady=3
            )

            ctk.CTkLabel(
                row,
                text=entry.filename,
                font=FONT_SMALL,
                text_color=COLOR_TEXT_PRIMARY,
                anchor="w",
            ).grid(row=0, column=1, sticky="w", padx=4)

            size_text = "" if entry.is_dir else human_size(entry.file_size)
            ctk.CTkLabel(
                row,
                text=size_text,
                font=FONT_MONO,
                text_color=COLOR_TEXT_SECONDARY,
            ).grid(row=0, column=2, padx=8)

        if len(self.filtered_entries) > self._display_limit:
            remaining = len(self.filtered_entries) - self._display_limit
            more_btn = ctk.CTkButton(
                self.contents_list,
                text=f"+ Xem thêm {remaining} mục khác...",
                **BTN_SECONDARY_STYLE,
                command=self._load_more_entries,
            )
            more_btn.pack(pady=6)

    def _load_more_entries(self):
        self._display_limit += 300
        self._render_entries()

    def _on_click_extract(self):
        zip_path = self.zip_path_entry.get().strip()
        dest_dir = self.dest_dir_entry.get().strip()

        if not zip_path or not Path(zip_path).exists():
            messagebox.showwarning("VietZIP", "Vui lòng chọn file ZIP hợp lệ!", parent=self.winfo_toplevel())
            return
        if not dest_dir:
            messagebox.showwarning("VietZIP", "Vui lòng chọn nơi để giải nén!", parent=self.winfo_toplevel())
            return

        password = self.pwd_entry.get().strip() or None
        self.on_start_extract(zip_path, dest_dir, password)

    def set_busy(self, is_busy: bool):
        self._is_busy = is_busy
        state = "disabled" if is_busy else "normal"
        self.btn_extract.configure(
            state=state,
            text="⏳ Đang giải nén..." if is_busy else "✨ Giải nén ngay!",
        )
