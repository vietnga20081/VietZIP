"""Tooltip nhẹ cho mọi widget (đặc biệt là icon-only button)."""

from __future__ import annotations

import tkinter as tk

from vietzip.ui.theme import FONT_SMALL, resolve_color, COLOR_SURFACE_ELEVATED, COLOR_TEXT_PRIMARY, COLOR_BORDER_STRONG


class Tooltip:
    def __init__(self, widget, text: str = "", delay_ms: int = 450):
        self.widget = widget
        self.text = text
        self.delay_ms = delay_ms
        self._job = None
        self._tip: tk.Toplevel | None = None
        for seq in ("<Enter>", "<Leave>", "<ButtonPress>", "<Destroy>"):
            widget.bind(seq, self._on_event, add="+")

    def set_text(self, text: str) -> None:
        self.text = text

    def _on_event(self, event) -> None:
        if event.type == tk.EventType.Enter:
            self._schedule()
        else:
            self._cancel()
            self._hide()

    def _schedule(self) -> None:
        self._cancel()
        if self.text:
            self._job = self.widget.after(self.delay_ms, self._show)

    def _cancel(self) -> None:
        if self._job is not None:
            try:
                self.widget.after_cancel(self._job)
            except Exception:
                pass
            self._job = None

    def _show(self) -> None:
        self._job = None
        if self._tip is not None or not self.text:
            return
        try:
            if not self.widget.winfo_exists():
                return
            x = self.widget.winfo_rootx() + 8
            y = self.widget.winfo_rooty() + self.widget.winfo_height() + 6
            tip = tk.Toplevel(self.widget)
            tip.wm_overrideredirect(True)
            tip.wm_geometry(f"+{x}+{y}")
            try:
                tip.attributes("-topmost", True)
            except Exception:
                pass
            frame = tk.Frame(
                tip,
                bg=resolve_color(COLOR_SURFACE_ELEVATED),
                highlightthickness=1,
                highlightbackground=resolve_color(COLOR_BORDER_STRONG),
            )
            frame.pack()
            tk.Label(
                frame,
                text=self.text,
                bg=resolve_color(COLOR_SURFACE_ELEVATED),
                fg=resolve_color(COLOR_TEXT_PRIMARY),
                font=FONT_SMALL,
                justify="left",
                wraplength=420,
                padx=8,
                pady=4,
            ).pack()
            self._tip = tip
        except Exception:
            self._tip = None

    def _hide(self) -> None:
        if self._tip is not None:
            try:
                self._tip.destroy()
            except Exception:
                pass
            self._tip = None
