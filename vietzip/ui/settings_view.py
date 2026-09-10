"""Settings window view."""

from __future__ import annotations

from tkinter import messagebox
import customtkinter as ctk

from vietzip.core.models import COMPRESSION_LEVELS, OverwritePolicy
from vietzip.services.context_menu_service import (
    is_context_menu_registered,
    register_context_menu,
    unregister_context_menu,
)
from vietzip.services.settings_service import settings_service
from vietzip.ui.theme import (
    COLOR_BORDER,
    COLOR_BTN_OUTLINE_TEXT,
    COLOR_CARD,
    COLOR_PRIMARY,
    COLOR_SEGMENT_TEXT,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    BTN_SECONDARY_STYLE,
    FONT_REGULAR,
    FONT_SECTION,
    FONT_SMALL,
)
from vietzip.utils.file_utils import get_asset_path


class SettingsWindow(ctk.CTkToplevel):
    """Cửa sổ cài đặt cấu hình VietZIP."""

    def __init__(self, master, on_theme_change=None):
        super().__init__(master)
        self.title("Cài đặt — VietZIP")
        self.geometry("540x510")
        self.minsize(500, 480)
        self.resizable(False, False)
        self.on_theme_change = on_theme_change

        ico_path = get_asset_path("vietzip.ico")
        if ico_path.exists():
            try:
                self.iconbitmap(str(ico_path))
            except Exception:
                pass

        self._build_layout()

    def _build_layout(self):
        self.grid_columnconfigure(0, weight=1)

        # Tabview Settings
        tabs = ctk.CTkTabview(
            self,
            corner_radius=12,
            text_color=COLOR_SEGMENT_TEXT,
            segmented_button_unselected_color=("#E2E8F0", "gray29"),
            segmented_button_unselected_hover_color=("#CBD5E1", "gray41"),
        )
        tabs.pack(fill="both", expand=True, padx=16, pady=(12, 10))

        tab_gen = tabs.add("Chung")
        tab_comp = tabs.add("Nén")
        tab_ext = tabs.add("Giải nén")
        tab_sys = tabs.add("Hệ thống")

        # ---- Tab Chung ----
        tab_gen.grid_columnconfigure(1, weight=1)

        # Theme
        ctk.CTkLabel(
            tab_gen, text="Giao diện (Theme):", font=FONT_REGULAR, text_color=COLOR_TEXT_PRIMARY
        ).grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.theme_menu = ctk.CTkOptionMenu(
            tab_gen,
            values=["System", "Light", "Dark"],
            command=self._on_theme_select,
        )
        self.theme_menu.set(settings_service.get("theme", "System"))
        self.theme_menu.grid(row=0, column=1, padx=10, pady=10, sticky="w")

        # Mascot
        self.mascot_var = ctk.BooleanVar(value=settings_service.get("show_mascot", True))
        ctk.CTkCheckBox(
            tab_gen,
            text="Hiển thị Mascot trạng thái ngộ nghĩnh",
            variable=self.mascot_var,
            font=FONT_REGULAR,
            text_color=COLOR_TEXT_PRIMARY,
        ).grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="w")

        # History
        self.history_var = ctk.BooleanVar(value=settings_service.get("history_enabled", True))
        ctk.CTkCheckBox(
            tab_gen,
            text="Tự động ghi nhớ lịch sử tác vụ",
            variable=self.history_var,
            font=FONT_REGULAR,
            text_color=COLOR_TEXT_PRIMARY,
        ).grid(row=2, column=0, columnspan=2, padx=10, pady=10, sticky="w")

        # Open folder after
        self.open_folder_var = ctk.BooleanVar(
            value=settings_service.get("open_folder_after_operation", True)
        )
        ctk.CTkCheckBox(
            tab_gen,
            text="Tự động mở thư mục sau khi hoàn thành",
            variable=self.open_folder_var,
            font=FONT_REGULAR,
            text_color=COLOR_TEXT_PRIMARY,
        ).grid(row=3, column=0, columnspan=2, padx=10, pady=10, sticky="w")

        # ---- Tab Nén ----
        tab_comp.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            tab_comp, text="Mức nén mặc định:", font=FONT_REGULAR, text_color=COLOR_TEXT_PRIMARY
        ).grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.comp_lvl_menu = ctk.CTkOptionMenu(
            tab_comp,
            values=list(COMPRESSION_LEVELS.keys()),
        )
        inv_map = {v: k for k, v in COMPRESSION_LEVELS.items()}
        self.comp_lvl_menu.set(inv_map.get(settings_service.get("compression_level", 6), "Cân bằng ⭐"))
        self.comp_lvl_menu.grid(row=0, column=1, padx=10, pady=10, sticky="w")

        self.verify_var = ctk.BooleanVar(value=settings_service.get("verify_archive", True))
        ctk.CTkCheckBox(
            tab_comp,
            text="Luôn xác minh CRC archive sau khi nén",
            variable=self.verify_var,
            font=FONT_REGULAR,
            text_color=COLOR_TEXT_PRIMARY,
        ).grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="w")

        # ---- Tab Giải nén ----
        tab_ext.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            tab_ext, text="Xử lý ghi đè file:", font=FONT_REGULAR, text_color=COLOR_TEXT_PRIMARY
        ).grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.overwrite_menu = ctk.CTkOptionMenu(
            tab_ext,
            values=["Tự động đổi tên", "Ghi đè", "Bỏ qua"],
        )
        cur_ow = settings_service.get("overwrite_policy", "auto_rename")
        ow_map = {"auto_rename": "Tự động đổi tên", "overwrite": "Ghi đè", "skip": "Bỏ qua"}
        self.overwrite_menu.set(ow_map.get(cur_ow, "Tự động đổi tên"))
        self.overwrite_menu.grid(row=0, column=1, padx=10, pady=10, sticky="w")

        self.warn_bomb_var = ctk.BooleanVar(value=settings_service.get("warn_large_archive", True))
        ctk.CTkCheckBox(
            tab_ext,
            text="Cảnh báo archive bất thường / Zip Bomb",
            variable=self.warn_bomb_var,
            font=FONT_REGULAR,
            text_color=COLOR_TEXT_PRIMARY,
        ).grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="w")

        ctk.CTkLabel(
            tab_ext, text="Ngưỡng cảnh báo dung lượng (GB):", font=FONT_REGULAR, text_color=COLOR_TEXT_PRIMARY
        ).grid(row=2, column=0, padx=10, pady=10, sticky="w")
        self.threshold_entry = ctk.CTkEntry(tab_ext, width=100, text_color=COLOR_TEXT_PRIMARY)
        self.threshold_entry.insert(0, str(settings_service.get("large_archive_threshold_gb", 10.0)))
        self.threshold_entry.grid(row=2, column=1, padx=10, pady=10, sticky="w")

        # ---- Tab Hệ thống (Menu chuột phải) ----
        tab_sys.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            tab_sys,
            text="Tích hợp Windows Explorer (Menu chuột phải):",
            font=FONT_SECTION,
            text_color=COLOR_TEXT_PRIMARY,
        ).pack(anchor="w", padx=10, pady=(10, 4))

        ctk.CTkLabel(
            tab_sys,
            text=(
                "Thêm lựa chọn 'Nén bằng VietZIP' và 'Giải nén bằng VietZIP' "
                "khi bấm chuột phải vào file/thư mục trong Windows Explorer."
            ),
            font=FONT_SMALL,
            wraplength=480,
            justify="left",
            text_color=COLOR_TEXT_SECONDARY,
        ).pack(anchor="w", padx=10, pady=(0, 12))

        self.ctx_status_lbl = ctk.CTkLabel(
            tab_sys,
            text="",
            font=FONT_REGULAR,
        )
        self.ctx_status_lbl.pack(anchor="w", padx=10, pady=(0, 10))

        ctx_btn_row = ctk.CTkFrame(tab_sys, fg_color="transparent")
        ctx_btn_row.pack(anchor="w", padx=10, pady=4)

        self.btn_reg_ctx = ctk.CTkButton(
            ctx_btn_row,
            text="➕ Thêm vào menu chuột phải",
            width=210,
            command=self._on_register_context_menu,
        )
        self.btn_reg_ctx.pack(side="left", padx=(0, 8))

        self.btn_unreg_ctx = ctk.CTkButton(
            ctx_btn_row,
            text="➖ Gỡ bỏ khỏi menu",
            width=160,
            **BTN_SECONDARY_STYLE,
            command=self._on_unregister_context_menu,
        )
        self.btn_unreg_ctx.pack(side="left")

        self._refresh_context_menu_status()

        # Bottom Buttons
        btn_box = ctk.CTkFrame(self, fg_color="transparent")
        btn_box.pack(fill="x", padx=16, pady=(0, 14))

        ctk.CTkButton(
            btn_box,
            text="ℹ️ Giới thiệu & Donate",
            width=160,
            **BTN_SECONDARY_STYLE,
            command=self._open_about,
        ).pack(side="left")

        ctk.CTkButton(
            btn_box,
            text="Lưu cài đặt",
            width=110,
            command=self._save_settings,
        ).pack(side="right", padx=(8, 0))

        ctk.CTkButton(
            btn_box,
            text="Hủy",
            width=80,
            **BTN_SECONDARY_STYLE,
            command=self.destroy,
        ).pack(side="right")

    def _open_about(self):
        from vietzip.ui.about_view import AboutWindow
        AboutWindow(self)

    def _refresh_context_menu_status(self):
        registered = is_context_menu_registered()
        if registered:
            self.ctx_status_lbl.configure(
                text="✓ Trạng thái: Đã tích hợp vào Menu chuột phải.",
                text_color="#10B981",
            )
            self.btn_reg_ctx.configure(state="disabled")
            self.btn_unreg_ctx.configure(state="normal")
        else:
            self.ctx_status_lbl.configure(
                text="○ Trạng thái: Chưa tích hợp vào Menu chuột phải.",
                text_color=COLOR_TEXT_SECONDARY,
            )
            self.btn_reg_ctx.configure(state="normal")
            self.btn_unreg_ctx.configure(state="disabled")

    def _on_register_context_menu(self):
        ok, msg = register_context_menu()
        if ok:
            messagebox.showinfo("Menu chuột phải", msg)
        else:
            messagebox.showerror("Lỗi", msg)
        self._refresh_context_menu_status()

    def _on_unregister_context_menu(self):
        ok, msg = unregister_context_menu()
        if ok:
            messagebox.showinfo("Menu chuột phải", msg)
        else:
            messagebox.showerror("Lỗi", msg)
        self._refresh_context_menu_status()

    def _on_theme_select(self, val):
        if self.on_theme_change:
            self.on_theme_change(val)

    def _save_settings(self):
        settings_service.set("theme", self.theme_menu.get())
        settings_service.set("show_mascot", self.mascot_var.get())
        settings_service.set("history_enabled", self.history_var.get())
        settings_service.set("open_folder_after_operation", self.open_folder_var.get())

        lvl_name = self.comp_lvl_menu.get()
        settings_service.set("compression_level", COMPRESSION_LEVELS.get(lvl_name, 6))
        settings_service.set("verify_archive", self.verify_var.get())

        inv_ow = {"Tự động đổi tên": "auto_rename", "Ghi đè": "overwrite", "Bỏ qua": "skip"}
        settings_service.set("overwrite_policy", inv_ow.get(self.overwrite_menu.get(), "auto_rename"))
        settings_service.set("warn_large_archive", self.warn_bomb_var.get())

        try:
            val = float(self.threshold_entry.get().strip())
            settings_service.set("large_archive_threshold_gb", val)
        except ValueError:
            pass

        self.destroy()
