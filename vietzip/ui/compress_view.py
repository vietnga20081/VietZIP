"""Compression tab view."""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from tkinter import filedialog
from typing import Callable, Optional
import customtkinter as ctk

from vietzip.core.models import COMPRESSION_LEVELS
from vietzip.services.settings_service import settings_service
from vietzip.ui.theme import (
    COLOR_CARD,
    COLOR_CARD_ALT,
    COLOR_BORDER,
    COLOR_PRIMARY,
    COLOR_BTN_OUTLINE_TEXT,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    BTN_SECONDARY_STYLE,
    FONT_MONO,
    FONT_REGULAR,
    FONT_SECTION,
    FONT_SMALL,
)
from vietzip.utils.file_utils import collect_items_to_compress
from vietzip.utils.format_utils import human_size


class CompressView(ctk.CTkFrame):
    """Giao diện tab Nén file & thư mục."""

    def __init__(
        self,
        master,
        on_start_compress: Callable[[list[str], str, int, Optional[str], bool], None],
        **kwargs,
    ):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.on_start_compress = on_start_compress

        self.compress_items: list[str] = []
        self._is_busy = False

        self._build_layout()

    def _build_layout(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Toolbar
        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.grid(row=0, column=0, sticky="ew", pady=(8, 6))

        ctk.CTkButton(
            toolbar,
            text="➕ Thêm file",
            width=120,
            command=self._add_files,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            toolbar,
            text="📁 Thêm thư mục",
            width=130,
            command=self._add_folder,
        ).pack(side="left", padx=8)

        self.btn_clear = ctk.CTkButton(
            toolbar,
            text="🗑️ Xóa hết",
            width=95,
            height=32,
            **BTN_SECONDARY_STYLE,
            command=self._clear_all,
        )
        self.btn_clear.pack(side="left", padx=8)

        # Realtime stats label on right
        self.stats_label = ctk.CTkLabel(
            toolbar,
            text="0 mục • 0 B",
            font=FONT_SMALL,
            text_color=COLOR_TEXT_SECONDARY,
        )
        self.stats_label.pack(side="right", padx=4)

        # File List Scrollable Box
        self.list_container = ctk.CTkScrollableFrame(
            self,
            corner_radius=12,
            border_width=1,
            border_color=COLOR_BORDER,
            fg_color=COLOR_CARD,
        )
        self.list_container.grid(row=1, column=0, sticky="nsew", pady=4)
        self.list_container.grid_columnconfigure(0, weight=1)

        self._render_empty_state()

        # Options Box
        options_card = ctk.CTkFrame(
            self,
            corner_radius=12,
            border_width=1,
            border_color=COLOR_BORDER,
            fg_color=COLOR_CARD,
        )
        options_card.grid(row=2, column=0, sticky="ew", pady=(8, 6), padx=2)
        options_card.grid_columnconfigure(1, weight=1)

        # Row 1: Compression Level & Verify
        r1 = ctk.CTkFrame(options_card, fg_color="transparent")
        r1.pack(fill="x", padx=12, pady=(10, 6))

        ctk.CTkLabel(r1, text="Mức nén:", font=FONT_REGULAR, text_color=COLOR_TEXT_PRIMARY).pack(side="left", padx=(0, 8))
        self.level_menu = ctk.CTkOptionMenu(
            r1,
            values=list(COMPRESSION_LEVELS.keys()),
            width=180,
            text_color="#FFFFFF",
        )
        # Lấy từ settings
        default_lvl = settings_service.get("compression_level", 6)
        inv_map = {v: k for k, v in COMPRESSION_LEVELS.items()}
        self.level_menu.set(inv_map.get(default_lvl, "Cân bằng ⭐"))
        self.level_menu.pack(side="left", padx=(0, 16))

        self.verify_var = ctk.BooleanVar(
            value=settings_service.get("verify_archive", True)
        )
        self.verify_chk = ctk.CTkCheckBox(
            r1,
            text="Xác minh archive sau khi nén (Verify CRC)",
            variable=self.verify_var,
            font=FONT_SMALL,
            text_color=COLOR_TEXT_PRIMARY,
        )
        self.verify_chk.pack(side="left")

        # Row 2: Password (AES-256)
        r2 = ctk.CTkFrame(options_card, fg_color="transparent")
        r2.pack(fill="x", padx=12, pady=(0, 10))

        ctk.CTkLabel(r2, text="🔐 Mật khẩu:", font=FONT_REGULAR, text_color=COLOR_TEXT_PRIMARY).pack(side="left", padx=(0, 8))
        self.pwd_entry = ctk.CTkEntry(
            r2,
            placeholder_text="Để trống nếu không mã hóa",
            show="•",
            width=220,
            text_color=COLOR_TEXT_PRIMARY,
        )
        self.pwd_entry.pack(side="left", padx=(0, 10))

        self.show_pwd_var = ctk.BooleanVar(value=False)
        self.show_pwd_chk = ctk.CTkCheckBox(
            r2,
            text="Hiện mật khẩu",
            variable=self.show_pwd_var,
            font=FONT_SMALL,
            text_color=COLOR_TEXT_PRIMARY,
            command=self._toggle_show_pwd,
        )
        self.show_pwd_chk.pack(side="left")

        # Big Compress Button
        self.btn_compress = ctk.CTkButton(
            self,
            text="🚀 Nén ngay!",
            height=46,
            font=("Segoe UI", 15, "bold"),
            command=self._on_click_compress,
        )
        self.btn_compress.grid(row=3, column=0, sticky="ew", pady=(4, 8))

    def _toggle_show_pwd(self):
        if self.show_pwd_var.get():
            self.pwd_entry.configure(show="")
        else:
            self.pwd_entry.configure(show="•")

    def _render_empty_state(self):
        for child in self.list_container.winfo_children():
            child.destroy()

        empty_box = ctk.CTkFrame(self.list_container, fg_color="transparent")
        empty_box.pack(pady=40)

        ctk.CTkLabel(
            empty_box,
            text="📥",
            font=("Segoe UI Emoji", 44),
        ).pack(pady=(0, 6))

        ctk.CTkLabel(
            empty_box,
            text="Kéo thả file hoặc thư mục vào đây",
            font=FONT_SECTION,
            text_color=COLOR_TEXT_PRIMARY,
        ).pack()

        ctk.CTkLabel(
            empty_box,
            text="hoặc sử dụng các nút phía trên để thêm nội dung cần nén",
            font=FONT_REGULAR,
            text_color=COLOR_TEXT_SECONDARY,
        ).pack(pady=(4, 0))

    def add_paths(self, paths: list[str]):
        """Thêm danh sách các đường dẫn (từ file dialog hoặc kéo thả)."""
        added = False
        for p in paths:
            clean = os.path.normpath(p)
            if clean not in self.compress_items and os.path.exists(clean):
                self.compress_items.append(clean)
                added = True
        if added:
            self.refresh_list_ui()

    def _add_files(self):
        files = filedialog.askopenfilenames(title="Chọn file cần nén", parent=self.winfo_toplevel())
        if files:
            self.add_paths(list(files))

    def _add_folder(self):
        folder = filedialog.askdirectory(title="Chọn thư mục cần nén", parent=self.winfo_toplevel())
        if folder:
            self.add_paths([folder])

    def _remove_item(self, path_str: str):
        if path_str in self.compress_items:
            self.compress_items.remove(path_str)
            self.refresh_list_ui()

    def _clear_all(self):
        self.compress_items.clear()
        self.refresh_list_ui()

    def refresh_list_ui(self):
        """Vẽ lại danh sách file trong list_container và cập nhật thống kê."""
        for child in self.list_container.winfo_children():
            child.destroy()

        if not self.compress_items:
            self._render_empty_state()
            self.stats_label.configure(text="0 mục • 0 B")
            return

        # Tính toán dung lượng và số lượng thực tế
        _, total_bytes, total_files, total_dirs = collect_items_to_compress(
            self.compress_items
        )
        self.stats_label.configure(
            text=f"{total_files} file, {total_dirs} thư mục • {human_size(total_bytes)}"
        )

        for p_str in self.compress_items:
            p = Path(p_str)
            is_dir = p.is_dir()
            icon = "📁" if is_dir else "📄"

            row = ctk.CTkFrame(
                self.list_container,
                corner_radius=8,
                fg_color=COLOR_CARD_ALT,
            )
            row.pack(fill="x", pady=2, padx=4)
            row.grid_columnconfigure(1, weight=1)

            ctk.CTkLabel(row, text=icon, font=("Segoe UI Emoji", 16)).grid(
                row=0, column=0, padx=(10, 6), pady=6
            )

            # File name & path
            name_box = ctk.CTkFrame(row, fg_color="transparent")
            name_box.grid(row=0, column=1, sticky="w", padx=4, pady=4)

            name_lbl = ctk.CTkLabel(
                name_box, text=p.name, font=FONT_REGULAR, text_color=COLOR_TEXT_PRIMARY, anchor="w"
            )
            name_lbl.pack(anchor="w")

            path_lbl = ctk.CTkLabel(
                name_box,
                text=str(p),
                font=FONT_SMALL,
                text_color=COLOR_TEXT_SECONDARY,
                anchor="w",
            )
            path_lbl.pack(anchor="w")

            # Size badge
            size_str = ""
            if not is_dir:
                try:
                    size_str = human_size(p.stat().st_size)
                except OSError:
                    size_str = "0 B"
            else:
                size_str = "Thư mục"

            ctk.CTkLabel(
                row,
                text=size_str,
                font=FONT_SMALL,
                text_color=COLOR_TEXT_SECONDARY,
            ).grid(row=0, column=2, padx=10)

            # Delete button
            del_btn = ctk.CTkButton(
                row,
                text="✕",
                width=28,
                height=28,
                fg_color="transparent",
                hover_color=("gray80", "gray25"),
                text_color=COLOR_BTN_OUTLINE_TEXT,
                command=lambda p_val=p_str: self._remove_item(p_val),
            )
            del_btn.grid(row=0, column=3, padx=(4, 8))

    def _on_click_compress(self):
        if not self.compress_items:
            from tkinter import messagebox
            messagebox.showwarning("VietZIP", "Vui lòng thêm ít nhất một file hoặc thư mục để nén!", parent=self.winfo_toplevel())
            return

        # Gợi ý tên file thông minh
        if len(self.compress_items) == 1:
            suggested_name = f"{Path(self.compress_items[0]).name}.zip"
        else:
            suggested_name = f"VietZIP_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"

        initial_dir = settings_service.get("default_output_dir")
        if not initial_dir or not Path(initial_dir).exists():
            initial_dir = str(Path(self.compress_items[0]).parent)

        output_path = filedialog.asksaveasfilename(
            title="Lưu file ZIP",
            defaultextension=".zip",
            initialdir=initial_dir,
            initialfile=suggested_name,
            filetypes=[("ZIP Archive", "*.zip")],
            parent=self.winfo_toplevel(),
        )
        if not output_path:
            return

        level_name = self.level_menu.get()
        level = COMPRESSION_LEVELS.get(level_name, 6)
        password = self.pwd_entry.get().strip() or None
        verify = self.verify_var.get()

        self.on_start_compress(
            list(self.compress_items),
            output_path,
            level,
            password,
            verify,
        )

    def set_busy(self, is_busy: bool):
        """Bật/tắt trạng thái đang nén của giao diện."""
        self._is_busy = is_busy
        state = "disabled" if is_busy else "normal"
        self.btn_compress.configure(
            state=state,
            text="⏳ Đang nén..." if is_busy else "🚀 Nén ngay!",
        )
        self.btn_clear.configure(state=state)
