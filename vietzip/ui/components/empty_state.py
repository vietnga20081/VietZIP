"""EmptyState tái sử dụng: [icon] Tiêu đề / Mô tả / [Hành động chính]."""

from __future__ import annotations

from typing import Callable, Optional

import customtkinter as ctk

from vietzip.ui.components.icon_button import AppButton
from vietzip.ui.icons import get_icon
from vietzip.ui.theme import (
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    FONT_BODY,
    FONT_SECTION,
    SP8,
    SP16,
    SP24,
)


class EmptyState(ctk.CTkFrame):
    def __init__(
        self,
        master,
        title: str,
        description: str = "",
        icon: str = "archive",
        action_text: Optional[str] = None,
        action: Optional[Callable[[], None]] = None,
        icon_size: int = 40,
        **kwargs,
    ):
        super().__init__(master, fg_color="transparent", **kwargs)
        ctk.CTkLabel(
            self, text="", image=get_icon(icon, icon_size, COLOR_TEXT_MUTED)
        ).pack(pady=(SP24, SP8))
        ctk.CTkLabel(
            self, text=title, font=FONT_SECTION, text_color=COLOR_TEXT_PRIMARY
        ).pack()
        if description:
            ctk.CTkLabel(
                self,
                text=description,
                font=FONT_BODY,
                text_color=COLOR_TEXT_SECONDARY,
                wraplength=380,
                justify="center",
            ).pack(pady=(4, 0))
        if action_text and action:
            AppButton(self, text=action_text, kind="primary", command=action).pack(
                pady=(SP16, SP24)
            )
        else:
            ctk.CTkFrame(self, height=SP24, fg_color="transparent").pack()
