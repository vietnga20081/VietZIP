"""ResultPanel: thẻ kết quả (Hoàn tất / Không thể hoàn thành) kèm hành động tiếp theo."""

from __future__ import annotations

from typing import Callable, Optional, Sequence

import customtkinter as ctk

from vietzip.ui.components.icon_button import AppButton
from vietzip.ui.icons import get_icon
from vietzip.ui.theme import (
    CARD_STYLE,
    COLOR_DANGER,
    COLOR_DANGER_SOFT,
    COLOR_SUCCESS,
    COLOR_SUCCESS_SOFT,
    COLOR_SURFACE_MUTED,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    COLOR_WARNING,
    COLOR_WARNING_SOFT,
    FONT_BODY,
    FONT_HEADING,
    FONT_MONO,
    FONT_SECTION,
    FONT_SMALL,
    R_LG,
    R_MD,
    SP4,
    SP8,
    SP12,
    SP16,
    SP24,
    SP32,
)
from vietzip.utils.format_utils import shorten_middle

Action = tuple[str, str, Callable[[], None]]  # (nhãn, kind, callback)


class ResultPanel(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self._card: Optional[ctk.CTkFrame] = None
        self._details_box: Optional[ctk.CTkTextbox] = None

    def _reset(self) -> ctk.CTkFrame:
        if self._card is not None:
            self._card.destroy()
        self._card = ctk.CTkFrame(self, **{**CARD_STYLE, "corner_radius": R_LG})
        self._card.grid(row=0, column=0, padx=SP32, pady=SP24)
        inner = ctk.CTkFrame(self._card, fg_color="transparent")
        inner.pack(padx=SP32, pady=SP32)
        return inner

    def _badge(self, parent, icon: str, fg, bg):
        circle = ctk.CTkFrame(parent, width=64, height=64, corner_radius=32, fg_color=bg)
        circle.pack_propagate(False)
        ctk.CTkLabel(circle, text="", image=get_icon(icon, 30, fg)).pack(expand=True)
        circle.pack()

    def _actions(self, parent, actions: Sequence[Action]):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(pady=(SP24, 0))
        for label, kind, cb in actions:
            AppButton(row, text=label, kind=kind, command=cb).pack(side="left", padx=SP4)
        return row

    # ------------------------------------------------------------------ Thành công
    def show_success(
        self,
        title: str,
        filename: str,
        lines: Sequence[str],
        actions: Sequence[Action],
        warnings: Sequence[str] = (),
    ) -> None:
        inner = self._reset()
        self._badge(inner, "check", COLOR_SUCCESS, COLOR_SUCCESS_SOFT)
        ctk.CTkLabel(inner, text=title, font=FONT_HEADING, text_color=COLOR_TEXT_PRIMARY).pack(pady=(SP16, SP4))
        ctk.CTkLabel(
            inner, text=shorten_middle(filename, 56), font=FONT_SECTION, text_color=COLOR_TEXT_PRIMARY
        ).pack()
        for ln in lines:
            ctk.CTkLabel(inner, text=ln, font=FONT_BODY, text_color=COLOR_TEXT_SECONDARY).pack(pady=(SP4, 0))

        if warnings:
            box = ctk.CTkFrame(inner, corner_radius=R_MD, fg_color=COLOR_WARNING_SOFT)
            box.pack(fill="x", pady=(SP16, 0))
            head = ctk.CTkLabel(
                box,
                text=f" Có {len(warnings)} cảnh báo trong quá trình xử lý",
                image=get_icon("warn", 16, COLOR_WARNING),
                compound="left",
                font=FONT_SMALL,
                text_color=COLOR_WARNING,
                anchor="w",
            )
            head.pack(fill="x", padx=SP12, pady=(SP8, SP4))
            shown = list(warnings[:5])
            text = "\n".join(f"• {shorten_middle(w, 90)}" for w in shown)
            if len(warnings) > 5:
                text += f"\n… và {len(warnings) - 5} cảnh báo khác (xem nhật ký)"
            ctk.CTkLabel(
                box, text=text, font=FONT_SMALL, text_color=COLOR_TEXT_SECONDARY, justify="left", anchor="w",
                wraplength=440,
            ).pack(fill="x", padx=SP12, pady=(0, SP8))
        self._actions(inner, actions)

    # ------------------------------------------------------------------ Lỗi
    def show_error(
        self,
        message: str,
        details: Optional[str],
        actions: Sequence[Action],
    ) -> None:
        inner = self._reset()
        self._badge(inner, "warn", COLOR_DANGER, COLOR_DANGER_SOFT)
        ctk.CTkLabel(
            inner, text="Không thể hoàn thành", font=FONT_HEADING, text_color=COLOR_TEXT_PRIMARY
        ).pack(pady=(SP16, SP8))
        ctk.CTkLabel(
            inner, text=message, font=FONT_BODY, text_color=COLOR_TEXT_SECONDARY, wraplength=440, justify="center"
        ).pack()

        row = ctk.CTkFrame(inner, fg_color="transparent")
        row.pack(pady=(SP24, 0))
        for label, kind, cb in actions:
            AppButton(row, text=label, kind=kind, command=cb).pack(side="left", padx=SP4)

        self._details_box = None
        if details:
            def toggle():
                if self._details_box is None:
                    return
                if self._details_box.winfo_ismapped():
                    self._details_box.pack_forget()
                    btn.configure(text="Chi tiết")
                else:
                    self._details_box.pack(fill="x", pady=(SP12, 0))
                    btn.configure(text="Ẩn chi tiết")

            btn = AppButton(row, text="Chi tiết", kind="ghost", command=toggle)
            btn.pack(side="left", padx=SP4)
            self._details_box = ctk.CTkTextbox(
                inner, height=90, width=440, font=FONT_MONO, fg_color=COLOR_SURFACE_MUTED,
                text_color=COLOR_TEXT_SECONDARY, corner_radius=R_MD, wrap="word",
            )
            self._details_box.insert("1.0", details)
            self._details_box.configure(state="disabled")
