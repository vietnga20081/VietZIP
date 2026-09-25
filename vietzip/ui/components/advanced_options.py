"""AdvancedOptions: khối thu gọn 'Tùy chọn nâng cao' + dòng tóm tắt lựa chọn hiện tại."""

from __future__ import annotations

import customtkinter as ctk

from vietzip.ui.components.icon_button import AppButton
from vietzip.ui.theme import (
    CARD_STYLE,
    COLOR_TEXT_MUTED,
    FONT_BODY,
    FONT_SMALL,
    SP4,
    SP8,
    SP12,
    SP16,
)


class AdvancedOptions(ctk.CTkFrame):
    def __init__(self, master, title: str = "Tùy chọn nâng cao", expanded: bool = False):
        super().__init__(master, **CARD_STYLE)
        self.grid_columnconfigure(0, weight=1)
        self._title = title
        self._expanded = False

        head = ctk.CTkFrame(self, fg_color="transparent")
        head.grid(row=0, column=0, sticky="ew", padx=SP8, pady=SP4)
        head.grid_columnconfigure(1, weight=1)
        self.toggle_btn = AppButton(
            head, text=title, kind="ghost", icon="chevron_right", height=32, font=FONT_BODY,
            command=self.toggle, anchor="w",
        )
        self.toggle_btn.grid(row=0, column=0, sticky="w")
        self.summary = ctk.CTkLabel(head, text="", font=FONT_SMALL, text_color=COLOR_TEXT_MUTED, anchor="e")
        self.summary.grid(row=0, column=1, sticky="e", padx=SP8)

        self.body = ctk.CTkFrame(self, fg_color="transparent")
        self.body.grid_columnconfigure(0, weight=1)
        if expanded:
            self.toggle(True)

    @property
    def expanded(self) -> bool:
        return self._expanded

    def toggle(self, expand: bool | None = None) -> None:
        self._expanded = (not self._expanded) if expand is None else expand
        if self._expanded:
            self.body.grid(row=1, column=0, sticky="ew", padx=SP16, pady=(0, SP12))
            self.toggle_btn.set_icon("chevron_down")
        else:
            self.body.grid_remove()
            self.toggle_btn.set_icon("chevron_right")

    def set_summary(self, text: str) -> None:
        self.summary.configure(text=text)
