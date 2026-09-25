"""AppHeader: Logo + tên app | Theme • Lịch sử • Cài đặt • Thêm (⋯)."""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from typing import Callable, Optional

import customtkinter as ctk

from vietzip.ui.components.icon_button import IconButton
from vietzip.ui.theme import (
    APP_NAME,
    APP_SUBTITLE,
    COLOR_BORDER,
    COLOR_PRIMARY,
    COLOR_SURFACE,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    FONT_SMALL,
    FONT_TITLE,
    SP4,
    SP8,
    SP12,
    SP24,
    resolve_color,
)
from vietzip.utils.format_utils import shorten_middle

THEME_LABELS = {"System": "Theo hệ thống", "Light": "Sáng", "Dark": "Tối"}


def make_menu(master) -> tk.Menu:
    """tk.Menu có màu theo theme hiện tại (Windows dùng menu gốc nên có thể bỏ qua màu)."""
    from vietzip.ui.theme import COLOR_SURFACE_ELEVATED

    return tk.Menu(
        master,
        tearoff=0,
        bg=resolve_color(COLOR_SURFACE_ELEVATED),
        fg=resolve_color(COLOR_TEXT_PRIMARY),
        activebackground=resolve_color(COLOR_PRIMARY),
        activeforeground="#FFFFFF",
        bd=0,
        relief="flat",
    )


def popup_below(menu: tk.Menu, widget) -> None:
    x = widget.winfo_rootx()
    y = widget.winfo_rooty() + widget.winfo_height() + 2
    try:
        menu.tk_popup(x, y)
    finally:
        menu.grab_release()


class AppHeader(ctk.CTkFrame):
    def __init__(
        self,
        master,
        logo_image: Optional[ctk.CTkImage],
        current_theme: str,
        on_theme: Callable[[str], None],
        on_history: Callable[[], None],
        on_settings: Callable[[], None],
        on_about: Callable[[], None],
        get_recent: Callable[[], list[str]],
        on_open_recent: Callable[[str], None],
        on_clear_recent: Callable[[], None],
    ):
        super().__init__(master, corner_radius=0, fg_color=COLOR_SURFACE, border_width=0)
        self._on_theme = on_theme
        self._get_recent = get_recent
        self._on_open_recent = on_open_recent
        self._on_clear_recent = on_clear_recent
        self._on_about = on_about
        self._theme_var = tk.StringVar(value=current_theme)

        self.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(self, text="", image=logo_image, width=40, height=40).grid(
            row=0, column=0, padx=(SP24, SP12), pady=SP8
        )

        titles = ctk.CTkFrame(self, fg_color="transparent")
        titles.grid(row=0, column=1, sticky="w")
        ctk.CTkLabel(titles, text=APP_NAME, font=FONT_TITLE, text_color=COLOR_TEXT_PRIMARY, anchor="w").pack(anchor="w")
        ctk.CTkLabel(titles, text=APP_SUBTITLE, font=FONT_SMALL, text_color=COLOR_TEXT_SECONDARY, anchor="w").pack(
            anchor="w"
        )

        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.grid(row=0, column=2, padx=(0, SP24))
        self.theme_btn = IconButton(actions, icon="contrast", tooltip="Giao diện: Sáng / Tối / Theo hệ thống",
                                    command=self._popup_theme)
        self.theme_btn.pack(side="left", padx=SP4)
        self.history_btn = IconButton(actions, icon="clock", tooltip="Lịch sử (Ctrl+H)", command=on_history)
        self.history_btn.pack(side="left", padx=SP4)
        self.settings_btn = IconButton(actions, icon="gear", tooltip="Cài đặt (Ctrl+,)", command=on_settings)
        self.settings_btn.pack(side="left", padx=SP4)
        self.more_btn = IconButton(actions, icon="more", tooltip="Thêm", command=self._popup_more)
        self.more_btn.pack(side="left", padx=SP4)

        ctk.CTkFrame(self, height=1, fg_color=COLOR_BORDER, corner_radius=0).grid(
            row=1, column=0, columnspan=3, sticky="ew"
        )

    def set_theme(self, theme: str) -> None:
        self._theme_var.set(theme)

    def _popup_theme(self):
        menu = make_menu(self)
        for key, label in THEME_LABELS.items():
            menu.add_radiobutton(
                label=label, value=key, variable=self._theme_var, command=lambda k=key: self._on_theme(k)
            )
        popup_below(menu, self.theme_btn)

    def _popup_more(self):
        menu = make_menu(self)
        recent = self._get_recent()
        sub = make_menu(menu)
        if recent:
            for path in recent:
                p = Path(path)
                sub.add_command(
                    label=f"{shorten_middle(p.name, 40)}   —   {shorten_middle(str(p.parent), 40)}",
                    command=lambda x=path: self._on_open_recent(x),
                )
            sub.add_separator()
            sub.add_command(label="Xóa danh sách gần đây", command=self._on_clear_recent)
        else:
            sub.add_command(label="(Chưa có file nào)", state="disabled")
        menu.add_cascade(label="Mở gần đây", menu=sub)
        menu.add_separator()
        menu.add_command(label="Giới thiệu VietZIP", command=self._on_about)
        popup_below(menu, self.more_btn)
