"""Cửa sổ Cài đặt: sidebar (Giao diện / Nén / Giải nén / Hệ thống) + Lưu / Hủy."""

from __future__ import annotations

import sys
from pathlib import Path
from tkinter import messagebox

import customtkinter as ctk

from vietzip.core.models import OverwritePolicy
from vietzip.services.context_menu_service import (
    is_context_menu_registered,
    register_context_menu,
    unregister_context_menu,
)
from vietzip.services.settings_service import get_config_dir, settings_service
from vietzip.ui.compress_view import LEVEL_CHOICES
from vietzip.ui.components import AppButton, StatusBadge
from vietzip.ui.theme import (
    COLOR_BG,
    COLOR_BORDER,
    COLOR_DANGER,
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
    SP4,
    SP8,
    SP12,
    SP16,
    SP20,
    SP24,
    SWITCH_STYLE,
)
from vietzip.ui.widgets import setup_toplevel_window
from vietzip.utils.file_utils import open_in_explorer

THEMES = {"Theo hệ thống": "System", "Sáng": "Light", "Tối": "Dark"}
OVERWRITE = {"Tự động đổi tên": "auto_rename", "Ghi đè": "overwrite", "Bỏ qua": "skip"}
NAMING = {"Theo tên file/thư mục nguồn": "smart", "VietZIP + ngày giờ": "timestamp"}
SECTIONS = ["Giao diện", "Nén", "Giải nén", "Hệ thống"]


def _inv(d: dict, value):
    return next((k for k, v in d.items() if v == value), next(iter(d)))


class SettingsWindow(ctk.CTkToplevel):
    def __init__(self, master, on_theme_change=None):
        super().__init__(master, fg_color=COLOR_BG)
        self.title("Cài đặt — VietZIP")
        self.minsize(640, 460)
        self.resizable(False, False)
        self._on_theme_change = on_theme_change
        self._original_theme = settings_service.get("theme", "System")
        setup_toplevel_window(self, master, 680, 500)
        self.protocol("WM_DELETE_WINDOW", self._cancel)
        self.bind("<Escape>", lambda e: self._cancel(), add="+")
        self._build()
        self._select("Giao diện")

    # ------------------------------------------------------------------ Khung
    def _build(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        side = ctk.CTkFrame(self, corner_radius=0, fg_color=COLOR_SURFACE, width=170)
        side.grid(row=0, column=0, sticky="ns")
        side.grid_propagate(False)
        ctk.CTkLabel(side, text="Cài đặt", font=FONT_HEADING, text_color=COLOR_TEXT_PRIMARY).pack(
            anchor="w", padx=SP20, pady=(SP20, SP12)
        )
        self._nav: dict[str, AppButton] = {}
        for name in SECTIONS:
            b = AppButton(side, text=name, kind="ghost", anchor="w", command=lambda n=name: self._select(n))
            b.pack(fill="x", padx=SP12, pady=2)
            self._nav[name] = b

        self.content = ctk.CTkFrame(self, fg_color="transparent")
        self.content.grid(row=0, column=1, sticky="nsew", padx=SP24, pady=SP20)
        self.content.grid_columnconfigure(0, weight=1)
        self._pages = {
            "Giao diện": self._page_ui(),
            "Nén": self._page_compress(),
            "Giải nén": self._page_extract(),
            "Hệ thống": self._page_system(),
        }

        foot = ctk.CTkFrame(self, fg_color="transparent")
        foot.grid(row=1, column=1, sticky="e", padx=SP24, pady=(0, SP16))
        AppButton(foot, text="Hủy", kind="secondary", width=90, command=self._cancel).pack(side="left", padx=SP4)
        AppButton(foot, text="Lưu", kind="primary", width=90, command=self._save).pack(side="left", padx=SP4)

    def _select(self, name: str):
        for n, page in self._pages.items():
            if n == name:
                page.grid(row=0, column=0, sticky="nsew")
            else:
                page.grid_remove()
        for n, b in self._nav.items():
            b.set_kind("secondary" if n == name else "ghost")

    def _page(self, title: str) -> ctk.CTkFrame:
        f = ctk.CTkFrame(self.content, fg_color="transparent")
        f.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(f, text=title, font=FONT_HEADING, text_color=COLOR_TEXT_PRIMARY).grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, SP16)
        )
        return f

    def _row_option(self, page, row, label, values, current):
        ctk.CTkLabel(page, text=label, font=FONT_BODY, text_color=COLOR_TEXT_PRIMARY).grid(
            row=row, column=0, sticky="w", pady=SP8, padx=(0, SP16)
        )
        m = ctk.CTkOptionMenu(page, values=values, width=230, **OPTION_STYLE)
        m.set(current)
        m.grid(row=row, column=1, sticky="w", pady=SP8)
        return m

    def _row_switch(self, page, row, label, value):
        var = ctk.BooleanVar(value=value)
        ctk.CTkLabel(page, text=label, font=FONT_BODY, text_color=COLOR_TEXT_PRIMARY).grid(
            row=row, column=0, sticky="w", pady=SP8, padx=(0, SP16)
        )
        ctk.CTkSwitch(page, text="", variable=var, width=44, **{k: v for k, v in SWITCH_STYLE.items() if k not in ("text_color", "font")}).grid(
            row=row, column=1, sticky="e", pady=SP8
        )
        return var

    # ------------------------------------------------------------------ Trang
    def _page_ui(self):
        p = self._page("Giao diện")
        self.theme_menu = self._row_option(p, 1, "Chế độ hiển thị", list(THEMES), _inv(THEMES, self._original_theme))
        self.theme_menu.configure(command=self._preview_theme)
        self._row_option(p, 2, "Ngôn ngữ", ["Tiếng Việt"], "Tiếng Việt").configure(state="disabled")
        self.mascot_var = self._row_switch(p, 3, "Hiển thị logo ở màn hình trống", settings_service.get("show_mascot", True))
        self.history_var = self._row_switch(p, 4, "Ghi lịch sử", settings_service.get("history_enabled", True))
        self.open_var = self._row_switch(p, 5, "Mở thư mục sau khi hoàn tất", settings_service.get("open_folder_after_operation", True))
        return p

    def _page_compress(self):
        p = self._page("Nén")
        names = [l for l, _v, _d in LEVEL_CHOICES]
        cur = next((l for l, v, _d in LEVEL_CHOICES if v == settings_service.get("compression_level", 6)), "Cân bằng")
        self.level_menu = self._row_option(p, 1, "Mức nén mặc định", names, cur)
        self.verify_var = self._row_switch(p, 2, "Xác minh CRC sau khi nén", settings_service.get("verify_archive", True))
        self.naming_menu = self._row_option(p, 3, "Cách đặt tên file ZIP", list(NAMING), _inv(NAMING, settings_service.get("filename_behavior", "smart")))
        ctk.CTkLabel(p, text="Thư mục lưu mặc định", font=FONT_BODY, text_color=COLOR_TEXT_PRIMARY).grid(
            row=4, column=0, sticky="w", pady=SP8, padx=(0, SP16)
        )
        row = ctk.CTkFrame(p, fg_color="transparent")
        row.grid(row=4, column=1, sticky="w")
        self.outdir_entry = ctk.CTkEntry(row, width=230, placeholder_text="Cùng thư mục với nguồn", **{**ENTRY_STYLE})
        self.outdir_entry.pack(side="left")
        cur_dir = settings_service.get("default_output_dir", "")
        if cur_dir:
            self.outdir_entry.insert(0, cur_dir)
        AppButton(row, text="Chọn...", kind="secondary", width=70, command=self._pick_outdir).pack(side="left", padx=SP8)
        return p

    def _page_extract(self):
        p = self._page("Giải nén")
        cur = _inv(OVERWRITE, settings_service.get("overwrite_policy", "auto_rename"))
        self.ow_menu = self._row_option(p, 1, "Khi file đã tồn tại", list(OVERWRITE), cur)
        self.sub_var = self._row_switch(p, 2, "Tạo thư mục con theo tên ZIP", settings_service.get("create_subfolder", True))
        self.bomb_var = self._row_switch(p, 3, "Cảnh báo archive bất thường (Zip Bomb)", settings_service.get("warn_large_archive", True))
        ctk.CTkLabel(p, text="Ngưỡng cảnh báo dung lượng (GB)", font=FONT_BODY, text_color=COLOR_TEXT_PRIMARY).grid(
            row=4, column=0, sticky="w", pady=SP8, padx=(0, SP16)
        )
        self.thr_entry = ctk.CTkEntry(p, width=100, **ENTRY_STYLE)
        self.thr_entry.insert(0, f"{float(settings_service.get('large_archive_threshold_gb', 10.0)):g}")
        self.thr_entry.grid(row=4, column=1, sticky="w")
        self.thr_msg = ctk.CTkLabel(p, text="", font=FONT_SMALL, text_color=COLOR_DANGER)
        self.thr_msg.grid(row=5, column=1, sticky="w")
        return p

    def _page_system(self):
        p = self._page("Hệ thống")
        ctk.CTkLabel(p, text="Menu chuột phải trong Windows Explorer", font=FONT_SECTION,
                     text_color=COLOR_TEXT_PRIMARY).grid(row=1, column=0, columnspan=2, sticky="w")
        ctk.CTkLabel(
            p, text="Thêm 'Nén bằng VietZIP' và 'Giải nén bằng VietZIP' khi bấm chuột phải vào file, thư mục hoặc .zip.",
            font=FONT_SMALL, text_color=COLOR_TEXT_SECONDARY, wraplength=380, justify="left", anchor="w",
        ).grid(row=2, column=0, columnspan=2, sticky="w", pady=(SP4, SP8))
        self.ctx_badge_holder = ctk.CTkFrame(p, fg_color="transparent")
        self.ctx_badge_holder.grid(row=3, column=0, columnspan=2, sticky="w")
        btns = ctk.CTkFrame(p, fg_color="transparent")
        btns.grid(row=4, column=0, columnspan=2, sticky="w", pady=SP8)
        self.btn_on = AppButton(btns, text="Bật menu chuột phải", kind="primary", command=self._ctx_on)
        self.btn_on.pack(side="left", padx=(0, SP8))
        self.btn_off = AppButton(btns, text="Tắt menu chuột phải", kind="secondary", command=self._ctx_off)
        self.btn_off.pack(side="left")
        ctk.CTkFrame(p, height=1, fg_color=COLOR_BORDER).grid(row=5, column=0, columnspan=2, sticky="ew", pady=SP16)
        links = ctk.CTkFrame(p, fg_color="transparent")
        links.grid(row=6, column=0, columnspan=2, sticky="w")
        AppButton(links, text="Mở thư mục cài đặt", kind="secondary", icon="folder", command=self._open_install).pack(side="left", padx=(0, SP8))
        AppButton(links, text="Mở thư mục nhật ký", kind="secondary", icon="folder", command=self._open_logs).pack(side="left")
        self._refresh_ctx()
        return p

    # ------------------------------------------------------------------ Hành động
    def _pick_outdir(self):
        from tkinter import filedialog
        d = filedialog.askdirectory(parent=self, title="Chọn thư mục lưu mặc định")
        if d:
            self.outdir_entry.delete(0, "end")
            self.outdir_entry.insert(0, d)

    def _preview_theme(self, label: str):
        if self._on_theme_change:
            self._on_theme_change(THEMES[label])  # xem trước ngay; Hủy sẽ hoàn tác

    def _refresh_ctx(self):
        for w in self.ctx_badge_holder.winfo_children():
            w.destroy()
        on = is_context_menu_registered()
        if on:
            StatusBadge(self.ctx_badge_holder, "success", "Đã bật").pack(side="left")
        else:
            StatusBadge(self.ctx_badge_holder, "info", "Chưa bật", icon="close").pack(side="left")
        self.btn_on.configure(state="disabled" if on else "normal")
        self.btn_off.configure(state="normal" if on else "disabled")
        if sys.platform != "win32":
            self.btn_on.configure(state="disabled")
            ctk.CTkLabel(self.ctx_badge_holder, text="  Chỉ khả dụng trên Windows", font=FONT_SMALL,
                         text_color=COLOR_TEXT_MUTED).pack(side="left")

    def _ctx_on(self):
        ok, msg = register_context_menu()
        (messagebox.showinfo if ok else messagebox.showerror)("Menu chuột phải", msg, parent=self)
        self._refresh_ctx()

    def _ctx_off(self):
        ok, msg = unregister_context_menu()
        (messagebox.showinfo if ok else messagebox.showerror)("Menu chuột phải", msg, parent=self)
        self._refresh_ctx()

    def _open_install(self):
        base = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parents[2]
        open_in_explorer(base)

    def _open_logs(self):
        for cand in (Path("logs").resolve(), get_config_dir()):
            if cand.exists():
                open_in_explorer(cand)
                return

    def _cancel(self):
        if self._on_theme_change and settings_service.get("theme", "System") != self._original_theme:
            self._on_theme_change(self._original_theme)
        self.destroy()

    def _save(self):
        try:
            thr = float(self.thr_entry.get().strip().replace(",", "."))
            if thr <= 0:
                raise ValueError
        except ValueError:
            self._select("Giải nén")
            self.thr_msg.configure(text="Nhập một số lớn hơn 0 (ví dụ 10).")
            return
        s = settings_service
        s.set("theme", THEMES[self.theme_menu.get()])
        s.set("show_mascot", self.mascot_var.get())
        s.set("history_enabled", self.history_var.get())
        s.set("open_folder_after_operation", self.open_var.get())
        s.set("compression_level", next(v for l, v, _d in LEVEL_CHOICES if l == self.level_menu.get()))
        s.set("verify_archive", self.verify_var.get())
        s.set("filename_behavior", NAMING[self.naming_menu.get()])
        s.set("default_output_dir", self.outdir_entry.get().strip())
        s.set("overwrite_policy", OverwritePolicy(OVERWRITE[self.ow_menu.get()]).value)
        s.set("create_subfolder", self.sub_var.get())
        s.set("warn_large_archive", self.bomb_var.get())
        s.set("large_archive_threshold_gb", thr)
        self._original_theme = s.get("theme")
        self.destroy()
