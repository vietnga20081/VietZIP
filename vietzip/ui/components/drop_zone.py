"""DropZone: vùng kéo & thả trung tâm với 5 trạng thái (normal/hover/dragging/invalid/processing)."""

from __future__ import annotations

from typing import Callable, Optional

import customtkinter as ctk

from vietzip.ui.components.icon_button import AppButton
from vietzip.ui.icons import get_icon
from vietzip.ui.theme import (
    COLOR_DROP_BORDER,
    COLOR_DANGER,
    COLOR_DANGER_SOFT,
    COLOR_PRIMARY,
    COLOR_PRIMARY_SOFT,
    COLOR_SURFACE,
    COLOR_SURFACE_MUTED,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    FONT_BODY,
    FONT_HEADING,
    FONT_SMALL,
    R_LG,
    SP8,
    SP12,
    SP16,
)

_VISUAL = {
    "normal": (COLOR_SURFACE, COLOR_DROP_BORDER),
    "hover": (COLOR_SURFACE, COLOR_PRIMARY),
    "dragging": (COLOR_PRIMARY_SOFT, COLOR_PRIMARY),
    "invalid": (COLOR_DANGER_SOFT, COLOR_DANGER),
    "processing": (COLOR_SURFACE_MUTED, COLOR_DROP_BORDER),
}

_TEXTS = {
    "compress": dict(
        title="Kéo file hoặc thư mục vào đây",
        compact="Kéo thả thêm file hoặc thư mục vào đây",
        hint="Ctrl + O: chọn file   ·   Ctrl + Shift + O: chọn thư mục",
    ),
    "extract": dict(
        title="Kéo file ZIP vào đây",
        compact="Kéo thả file ZIP khác vào đây để đổi",
        hint="Ctrl + O: chọn file ZIP",
    ),
}


class DropZone(ctk.CTkFrame):
    def __init__(
        self,
        master,
        on_pick_files: Callable[[], None],
        on_pick_folder: Optional[Callable[[], None]] = None,
        mode: str = "compress",
        logo_image: Optional[ctk.CTkImage] = None,
        **kwargs,
    ):
        super().__init__(
            master,
            corner_radius=R_LG,
            border_width=2,
            fg_color=COLOR_SURFACE,
            border_color=COLOR_DROP_BORDER,
            **kwargs,
        )
        self._on_pick_files = on_pick_files
        self._on_pick_folder = on_pick_folder
        self._mode = mode
        self._logo_image = logo_image
        self._state = "normal"
        self._hover = False
        self._compact = False

        self._build_full()
        self._build_compact()
        self._show_layout()
        self.set_mode(mode)

        self._bind_interaction(self)

    # ------------------------------------------------------------ dựng UI
    def _build_full(self):
        self.full = ctk.CTkFrame(self, fg_color="transparent")
        inner = ctk.CTkFrame(self.full, fg_color="transparent")
        inner.place(relx=0.5, rely=0.5, anchor="center")

        icon = self._logo_image or get_icon("drop", 44, COLOR_TEXT_MUTED)
        self.full_icon = ctk.CTkLabel(inner, text="", image=icon)
        self.full_icon.pack(pady=(0, SP12))
        self.full_title = ctk.CTkLabel(inner, text="", font=FONT_HEADING, text_color=COLOR_TEXT_PRIMARY)
        self.full_title.pack()
        self.full_sub = ctk.CTkLabel(
            inner, text="Hoặc chọn từ máy tính", font=FONT_BODY, text_color=COLOR_TEXT_SECONDARY
        )
        self.full_sub.pack(pady=(4, SP16))

        row = ctk.CTkFrame(inner, fg_color="transparent")
        row.pack()
        self.btn_files = AppButton(row, text="Chọn file", kind="primary", icon="file", command=self._on_pick_files)
        self.btn_files.pack(side="left", padx=(0, SP8))
        self.btn_folder = AppButton(
            row, text="Chọn thư mục", kind="secondary", icon="folder", command=self._pick_folder
        )
        self.btn_folder.pack(side="left")

        self.full_hint = ctk.CTkLabel(inner, text="", font=FONT_SMALL, text_color=COLOR_TEXT_MUTED)
        self.full_hint.pack(pady=(SP16, 0))

    def _build_compact(self):
        self.compact = ctk.CTkFrame(self, fg_color="transparent")
        self.compact.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(self.compact, text="", image=get_icon("drop", 22, COLOR_TEXT_MUTED)).grid(
            row=0, column=0, padx=(SP16, SP12), pady=SP12
        )
        self.compact_title = ctk.CTkLabel(
            self.compact, text="", font=FONT_BODY, text_color=COLOR_TEXT_SECONDARY, anchor="w"
        )
        self.compact_title.grid(row=0, column=1, sticky="w")
        self.cbtn_files = AppButton(
            self.compact, text="Chọn file", kind="secondary", height=32, command=self._on_pick_files
        )
        self.cbtn_files.grid(row=0, column=2, padx=(SP8, 0))
        self.cbtn_folder = AppButton(
            self.compact, text="Chọn thư mục", kind="secondary", height=32, command=self._pick_folder
        )
        self.cbtn_folder.grid(row=0, column=3, padx=(SP8, SP12))

    def _pick_folder(self):
        if self._on_pick_folder:
            self._on_pick_folder()

    def _show_layout(self):
        self.full.pack_forget()
        self.compact.pack_forget()
        if self._compact:
            self.compact.pack(fill="x")
            self.configure(height=56)
        else:
            self.full.pack(fill="both", expand=True)
            self.configure(height=200)
        self._bind_interaction(self)

    # ------------------------------------------------------------ API
    def set_mode(self, mode: str) -> None:
        self._mode = mode
        t = _TEXTS[mode]
        self.full_title.configure(text=t["title"])
        self.full_hint.configure(text=t["hint"])
        self.compact_title.configure(text=t["compact"])
        is_compress = mode == "compress"
        files_text = "Chọn file" if is_compress else "Chọn file ZIP"
        self.btn_files.configure(text=files_text)
        self.cbtn_files.configure(text=files_text)
        if is_compress:
            self.btn_folder.pack(side="left")
            self.cbtn_folder.grid()
        else:
            self.btn_folder.pack_forget()
            self.cbtn_folder.grid_remove()

    def set_compact(self, compact: bool) -> None:
        if compact != self._compact:
            self._compact = compact
            self._show_layout()

    @property
    def is_compact(self) -> bool:
        return self._compact

    def set_state(self, state: str) -> None:
        """state: normal | dragging | invalid | processing"""
        self._state = state
        if state == "dragging":
            self.full_title.configure(text="Thả vào đây để thêm")
            self.compact_title.configure(text="Thả vào đây để thêm")
        elif state == "invalid":
            self.full_title.configure(text="Không đọc được dữ liệu vừa thả")
            self.compact_title.configure(text="Không đọc được dữ liệu vừa thả")
        else:
            t = _TEXTS[self._mode]
            self.full_title.configure(text=t["title"])
            self.compact_title.configure(text=t["compact"])
        busy = state == "processing"
        for b in (self.btn_files, self.btn_folder, self.cbtn_files, self.cbtn_folder):
            b.configure(state="disabled" if busy else "normal")
        self._apply_visual()

    @property
    def state(self) -> str:
        return self._state

    def _apply_visual(self) -> None:
        key = self._state
        if key == "normal" and self._hover:
            key = "hover"
        fg, border = _VISUAL[key]
        self.configure(fg_color=fg, border_color=border)

    # ------------------------------------------------------------ tương tác
    def _bind_interaction(self, widget) -> None:
        for child in widget.winfo_children():
            if not isinstance(child, AppButton):
                child.bind("<Button-1>", self._on_click, add="+")
            child.bind("<Enter>", self._on_enter, add="+")
            child.bind("<Leave>", self._on_leave, add="+")
            self._bind_interaction(child)
        widget.bind("<Enter>", self._on_enter, add="+")
        widget.bind("<Leave>", self._on_leave, add="+")
        if widget is self:
            widget.bind("<Button-1>", self._on_click, add="+")

    def _on_click(self, _e=None):
        if self._state in ("normal", "invalid"):
            self._on_pick_files()

    def _on_enter(self, _e=None):
        if not self._hover:
            self._hover = True
            self._apply_visual()

    def _on_leave(self, _e=None):
        self.after(40, self._check_leave)

    def _check_leave(self):
        try:
            x, y = self.winfo_pointerxy()
            w = self.winfo_containing(x, y)
        except Exception:
            w = None
        inside = False
        while w is not None:
            if w is self:
                inside = True
                break
            w = getattr(w, "master", None)
        if not inside and self._hover:
            self._hover = False
            self._apply_visual()
