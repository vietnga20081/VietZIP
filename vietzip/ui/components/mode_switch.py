"""ModeSwitch: công tắc 2 chế độ lớn NÉN | GIẢI NÉN."""

from __future__ import annotations

from typing import Callable

import customtkinter as ctk

from vietzip.ui.components.icon_button import AppButton
from vietzip.ui.theme import COLOR_SURFACE_MUTED, FONT_SECTION, R_LG, SP4

MODES = {
    "compress": ("Nén file", "archive"),
    "extract": ("Giải nén", "open"),
}


class ModeSwitch(ctk.CTkFrame):
    def __init__(self, master, on_change: Callable[[str], None]):
        super().__init__(master, corner_radius=R_LG, fg_color=COLOR_SURFACE_MUTED)
        self._on_change = on_change
        self._mode = "compress"
        self._buttons: dict[str, AppButton] = {}
        for i, (key, (label, icon)) in enumerate(MODES.items()):
            btn = AppButton(
                self, text=label, kind="ghost", icon=icon, icon_size=18, width=170, height=40,
                font=FONT_SECTION, corner_radius=R_LG - 3, command=lambda k=key: self.select(k),
            )
            btn.grid(row=0, column=i, padx=SP4, pady=SP4)
            self._buttons[key] = btn
        self._refresh()

    @property
    def mode(self) -> str:
        return self._mode

    def select(self, mode: str, notify: bool = True) -> None:
        if mode == self._mode:
            return
        self._mode = mode
        self._refresh()
        if notify:
            self._on_change(mode)

    def set_enabled(self, enabled: bool) -> None:
        for b in self._buttons.values():
            b.configure(state="normal" if enabled else "disabled")

    def _refresh(self) -> None:
        for key, btn in self._buttons.items():
            btn.set_kind("primary" if key == self._mode else "ghost")
