"""OutputPicker: ô đường dẫn + nút chọn + thông báo lỗi/cảnh báo ngay cạnh field."""

from __future__ import annotations

from typing import Callable, Optional

import customtkinter as ctk

from vietzip.ui.components.icon_button import AppButton
from vietzip.ui.components.tooltip import Tooltip
from vietzip.ui.icons import get_icon
from vietzip.ui.theme import (
    COLOR_DANGER,
    COLOR_FOCUS,
    COLOR_TEXT_PRIMARY,
    COLOR_WARNING,
    ENTRY_STYLE,
    FONT_SECTION,
    FONT_SMALL,
    SP4,
    SP8,
)


class OutputPicker(ctk.CTkFrame):
    def __init__(
        self,
        master,
        label: str,
        placeholder: str = "",
        browse_text: str = "Chọn...",
        on_browse: Optional[Callable[[], None]] = None,
        on_edit: Optional[Callable[[], None]] = None,
    ):
        super().__init__(master, fg_color="transparent")
        self.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(self, text=label, font=FONT_SECTION, text_color=COLOR_TEXT_PRIMARY, anchor="w").grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, SP4)
        )
        self.entry = ctk.CTkEntry(self, placeholder_text=placeholder, **ENTRY_STYLE)
        self.entry.grid(row=1, column=0, sticky="ew", padx=(0, SP8))
        self.btn = AppButton(self, text=browse_text, kind="secondary", command=on_browse or (lambda: None))
        self.btn.grid(row=1, column=1)
        self.msg = ctk.CTkLabel(self, text="", font=FONT_SMALL, anchor="w", justify="left", compound="left")
        self.msg.grid(row=2, column=0, columnspan=2, sticky="w", pady=(SP4, 0))
        self.msg.grid_remove()

        self._tip = Tooltip(self.entry, "")
        self._on_edit = on_edit
        self.entry.bind("<KeyRelease>", self._edited, add="+")
        self.entry.bind("<FocusIn>", lambda e: self.entry.configure(border_color=COLOR_FOCUS), add="+")
        self.entry.bind("<FocusOut>", lambda e: self.entry.configure(border_color=ENTRY_STYLE["border_color"]), add="+")

    def _edited(self, _e=None):
        self._tip.set_text(self.get())
        if self._on_edit:
            self._on_edit()

    def get(self) -> str:
        return self.entry.get().strip()

    def set(self, value: str) -> None:
        self.entry.delete(0, "end")
        self.entry.insert(0, value)
        self._tip.set_text(value)

    def set_enabled(self, enabled: bool) -> None:
        st = "normal" if enabled else "disabled"
        self.entry.configure(state=st)
        self.btn.configure(state=st)

    def set_message(self, text: Optional[str], kind: str = "error") -> None:
        """kind: error | warning. text=None để ẩn."""
        if not text:
            self.msg.grid_remove()
            return
        color = COLOR_DANGER if kind == "error" else COLOR_WARNING
        icon = "error" if kind == "error" else "warn"
        self.msg.configure(text=f" {text}", text_color=color, image=get_icon(icon, 14, color), wraplength=520)
        self.msg.grid()
        self.entry.configure(border_color=color if kind == "error" else ENTRY_STYLE["border_color"])

    def clear_message(self) -> None:
        self.set_message(None)
        self.entry.configure(border_color=ENTRY_STYLE["border_color"])
