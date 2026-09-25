"""AppButton (nút chuẩn, có focus ring + bàn phím) và IconButton (nút chỉ có icon + tooltip)."""

from __future__ import annotations

import tkinter as tk
from typing import Optional

import customtkinter as ctk

from vietzip.ui.components.tooltip import Tooltip
from vietzip.ui.icons import get_icon
from vietzip.ui.theme import (
    BUTTON_STYLES,
    COLOR_DISABLED_FILL,
    COLOR_DISABLED_TEXT,
    COLOR_FOCUS,
    COLOR_TEXT_ON_PRIMARY,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    FONT_BODY,
    R_SM,
)

_ICON_COLOR = {
    "primary": COLOR_TEXT_ON_PRIMARY,
    "danger": COLOR_TEXT_ON_PRIMARY,
    "secondary": COLOR_TEXT_PRIMARY,
    "ghost": COLOR_TEXT_SECONDARY,
}


class AppButton(ctk.CTkButton):
    """CTkButton + style theo `kind` + điều hướng bàn phím (Tab, Enter, Space) + focus ring."""

    def __init__(
        self,
        master,
        text: str = "",
        kind: str = "secondary",
        icon: Optional[str] = None,
        icon_size: int = 16,
        tooltip: Optional[str] = None,
        **kwargs,
    ):
        style = dict(BUTTON_STYLES[kind])
        style.setdefault("corner_radius", R_SM)
        style.setdefault("height", 36)
        style.setdefault("font", FONT_BODY)
        style.update(kwargs)
        self.kind = kind
        self._icon_name = icon
        self._icon_size = icon_size
        self._base_border_w = style.get("border_width", 0)
        self._base_border_c = style.get("border_color")
        if icon:
            style["image"] = get_icon(icon, icon_size, _ICON_COLOR[kind])
            style.setdefault("compound", "left")
        super().__init__(master, text=text, **style)

        self._tooltip = Tooltip(self, tooltip) if tooltip else None
        try:  # cho phép Tab chọn nút
            tk.Frame.configure(self, takefocus=True)
        except Exception:
            pass
        tk.Misc.bind(self, "<FocusIn>", self._focus_in, add="+")
        tk.Misc.bind(self, "<FocusOut>", self._focus_out, add="+")
        tk.Misc.bind(self, "<Return>", self._activate, add="+")
        tk.Misc.bind(self, "<space>", self._activate, add="+")

    def configure(self, require_redraw=False, **kwargs):
        super().configure(require_redraw=require_redraw, **kwargs)
        if "state" in kwargs:
            self._paint_state()

    def _paint_state(self) -> None:
        """Nút đặc (primary/danger) khi bị vô hiệu phải nhìn thấy rõ là không bấm được."""
        if self.kind not in ("primary", "danger"):
            return
        st = BUTTON_STYLES[self.kind]
        if str(self.cget("state")) == "disabled":
            super().configure(fg_color=COLOR_DISABLED_FILL, hover_color=COLOR_DISABLED_FILL,
                              text_color_disabled=COLOR_DISABLED_TEXT)
        else:
            super().configure(fg_color=st["fg_color"], hover_color=st["hover_color"])

    def set_icon(self, name: str, kind: Optional[str] = None) -> None:
        self._icon_name = name
        self.configure(image=get_icon(name, self._icon_size, _ICON_COLOR[kind or self.kind]))

    def set_kind(self, kind: str) -> None:
        """Đổi kiểu nút (primary/secondary/ghost/danger) khi đang chạy."""
        st = BUTTON_STYLES[kind]
        self.kind = kind
        self._base_border_w = st.get("border_width", 0)
        self._base_border_c = st.get("border_color")
        opts = {k: st[k] for k in ("fg_color", "hover_color", "text_color", "text_color_disabled", "border_width") if k in st}
        if "border_color" in st:
            opts["border_color"] = st["border_color"]
        self.configure(**opts)
        if self._icon_name:
            self.set_icon(self._icon_name, kind)
        self._paint_state()

    def _focus_in(self, _e=None):
        try:
            self.configure(border_width=2, border_color=COLOR_FOCUS)
        except Exception:
            pass

    def _focus_out(self, _e=None):
        try:
            self.configure(border_width=self._base_border_w)
            if self._base_border_c is not None:
                self.configure(border_color=self._base_border_c)
        except Exception:
            pass

    def _activate(self, _e=None):
        if str(self.cget("state")) != "disabled":
            self.invoke()
        return "break"


class IconButton(AppButton):
    """Nút vuông chỉ có icon. Bắt buộc có tooltip để rõ nghĩa."""

    def __init__(
        self,
        master,
        icon: str,
        tooltip: str,
        kind: str = "ghost",
        size: int = 36,
        icon_size: int = 18,
        **kwargs,
    ):
        super().__init__(
            master,
            text="",
            kind=kind,
            icon=icon,
            icon_size=icon_size,
            tooltip=tooltip,
            width=size,
            height=size,
            **kwargs,
        )
