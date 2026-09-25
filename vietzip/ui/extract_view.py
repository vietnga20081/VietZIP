"""Màn hình Giải nén: chọn ZIP → xem trước → nơi giải nén → tùy chọn → Giải nén ngay."""

from __future__ import annotations

import os
import queue
import threading
from pathlib import Path
from tkinter import filedialog, messagebox
from typing import Callable, Optional

import customtkinter as ctk

from vietzip.core.archive_info import get_archive_metadata, list_archive_entries
from vietzip.core.models import ArchiveEntry, ArchiveMetadata, OverwritePolicy
from vietzip.services.recent_service import recent_service
from vietzip.services.settings_service import settings_service
from vietzip.ui.components import (
    AdvancedOptions,
    AppButton,
    DropZone,
    EmptyState,
    IconButton,
    OutputPicker,
    StatusBadge,
)
from vietzip.ui.icons import get_icon
from vietzip.ui.archive_contents_view import ArchiveContentsWindow
from vietzip.ui.theme import (
    CARD_STYLE,
    CHECKBOX_STYLE,
    COLOR_DANGER,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    COLOR_WARNING,
    COLOR_WARNING_SOFT,
    ENTRY_STYLE,
    FONT_BUTTON_LG,
    FONT_SECTION,
    FONT_SMALL,
    R_SM,
    RADIO_STYLE,
    SP4,
    SP8,
    SP12,
    SP16,
)
from vietzip.ui.widgets import bring_to_front, get_logo_image
from vietzip.utils.error_utils import friendly_error
from vietzip.utils.format_utils import format_count, human_size, shorten_middle
from vietzip.utils.path_utils import suggest_extract_dir, validate_dest_dir

POLICY_CHOICES = [
    ("Tự động đổi tên — khuyến nghị", OverwritePolicy.AUTO_RENAME),
    ("Ghi đè file cũ", OverwritePolicy.OVERWRITE),
    ("Bỏ qua file đã có", OverwritePolicy.SKIP),
]
POLICY_SHORT = {
    OverwritePolicy.AUTO_RENAME: "Tự động đổi tên",
    OverwritePolicy.OVERWRITE: "Ghi đè",
    OverwritePolicy.SKIP: "Bỏ qua",
}


def is_zip(path: str) -> bool:
    return path.lower().endswith(".zip")


class ExtractView(ctk.CTkFrame):
    """Giao diện Giải nén. Không chứa logic giải nén — chỉ thu thập lựa chọn rồi gọi `on_start`."""

    def __init__(
        self,
        master,
        on_start: Callable[[str, str, Optional[str], OverwritePolicy], None],
        notify: Callable[[str, str, str], None],
        **kwargs,
    ):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.on_start = on_start
        self.notify = notify

        self.zip_path: Optional[str] = None
        self.meta: Optional[ArchiveMetadata] = None
        self.entries: list[ArchiveEntry] = []
        self._loading = False
        self._load_token = 0
        self._load_q: queue.Queue = queue.Queue()
        self._dest_dirty = False       # người dùng tự gõ đường dẫn
        self._dest_user_base = ""     # thư mục gốc chọn qua nút Chọn...
        self._busy = False
        self._eye_visible = False
        self._contents_win: Optional[ArchiveContentsWindow] = None

        self._build()
        self._refresh_layout()

    # ------------------------------------------------------------------ Dựng UI
    def _build(self):
        self.drop = DropZone(
            self,
            on_pick_files=self.pick_zip,
            mode="extract",
            logo_image=get_logo_image(64) if settings_service.get("show_mascot", True) else None,
        )

        # Slot xem trước: chứa thẻ archive hoặc trạng thái lỗi
        self.preview_slot = ctk.CTkFrame(self, fg_color="transparent")
        self.preview_slot.grid_columnconfigure(0, weight=1)
        self._build_preview_card()

        self.pwd_row = ctk.CTkFrame(self, fg_color="transparent")
        self._build_password(self.pwd_row)

        self.dest_holder = ctk.CTkFrame(self, fg_color="transparent")
        self.dest_holder.grid_columnconfigure(0, weight=1)
        self.dest = OutputPicker(
            self.dest_holder, label="Giải nén vào", placeholder="Chọn thư mục giải nén...",
            browse_text="Chọn...", on_browse=self._browse_dest, on_edit=self._on_dest_edited,
        )
        self.dest.grid(row=0, column=0, sticky="ew")
        self.subfolder_var = ctk.BooleanVar(value=settings_service.get("create_subfolder", True))
        ctk.CTkCheckBox(
            self.dest_holder, text="Tạo thư mục con theo tên file ZIP", variable=self.subfolder_var,
            command=self._on_subfolder_toggle, **CHECKBOX_STYLE,
        ).grid(row=1, column=0, sticky="w", pady=(SP8, 0))

        self.advanced = AdvancedOptions(self)
        self._build_advanced(self.advanced.body)

        self.btn_start = AppButton(
            self, text="Giải nén ngay", kind="primary", icon="open", icon_size=20, height=48,
            font=FONT_BUTTON_LG, command=self._on_click_start,
        )

    def _build_preview_card(self):
        self.card = ctk.CTkFrame(self.preview_slot, **CARD_STYLE)
        self.card.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(self.card, text="", image=get_icon("archive", 30, COLOR_TEXT_SECONDARY)).grid(
            row=0, column=0, rowspan=2, padx=(SP16, SP12), pady=SP12
        )
        head = ctk.CTkFrame(self.card, fg_color="transparent")
        head.grid(row=0, column=1, sticky="w", pady=(SP12, 0))
        self.name_lbl = ctk.CTkLabel(head, text="", font=FONT_SECTION, text_color=COLOR_TEXT_PRIMARY, anchor="w")
        self.name_lbl.pack(side="left")
        self.badges = ctk.CTkFrame(head, fg_color="transparent")
        self.badges.pack(side="left", padx=SP8)
        self.meta_lbl = ctk.CTkLabel(self.card, text="", font=FONT_SMALL, text_color=COLOR_TEXT_SECONDARY, anchor="w")
        self.meta_lbl.grid(row=1, column=1, sticky="w", pady=(0, SP12))
        self.btn_toggle = AppButton(
            self.card, text="Xem nội dung", kind="secondary", height=32, command=self._open_contents
        )
        self.btn_toggle.grid(row=0, column=2, rowspan=2, padx=SP12)

        self.warn_box = ctk.CTkFrame(self.card, corner_radius=R_SM, fg_color=COLOR_WARNING_SOFT)
        self.warn_lbl = ctk.CTkLabel(
            self.warn_box, text="", image=get_icon("warn", 16, COLOR_WARNING), compound="left",
            font=FONT_SMALL, text_color=COLOR_WARNING, justify="left", anchor="w", wraplength=640,
        )
        self.warn_lbl.pack(fill="x", padx=SP12, pady=SP8)

    def _build_password(self, parent):
        parent.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            parent, text="Mật khẩu (archive này được mã hóa)", font=FONT_SECTION,
            text_color=COLOR_TEXT_PRIMARY, anchor="w", height=20,
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, SP4))
        self.pwd_entry = ctk.CTkEntry(parent, placeholder_text="Nhập mật khẩu", show="•", **ENTRY_STYLE)
        self.pwd_entry.grid(row=1, column=0, sticky="ew", padx=(0, SP8))
        self.pwd_entry.bind("<KeyRelease>", lambda e: self._validate(), add="+")
        self.pwd_entry.bind("<Return>", lambda e: self._on_click_start(), add="+")
        self.btn_eye = IconButton(parent, icon="eye", tooltip="Hiện/ẩn mật khẩu", command=self._toggle_pwd, size=36)
        self.btn_eye.grid(row=1, column=1)

    def _build_advanced(self, body):
        ctk.CTkLabel(
            body, text="Khi file đã tồn tại", font=FONT_SECTION, text_color=COLOR_TEXT_PRIMARY, anchor="w"
        ).grid(row=0, column=0, sticky="w", pady=(0, SP4))
        try:
            default = OverwritePolicy(settings_service.get("overwrite_policy", "auto_rename"))
        except ValueError:
            default = OverwritePolicy.AUTO_RENAME
        self.policy_var = ctk.StringVar(value=default.value)
        for i, (label, pol) in enumerate(POLICY_CHOICES):
            ctk.CTkRadioButton(
                body, text=label, variable=self.policy_var, value=pol.value,
                command=self._on_policy_changed, **RADIO_STYLE,
            ).grid(row=1 + i, column=0, sticky="w", pady=SP4)
        self.policy_warn = ctk.CTkLabel(
            body, text=" Các file trùng tên sẽ bị ghi đè và không thể khôi phục.",
            image=get_icon("warn", 14, COLOR_DANGER), compound="left", font=FONT_SMALL,
            text_color=COLOR_DANGER, anchor="w",
        )
        self.policy_warn.grid(row=4, column=0, sticky="w", pady=(SP4, 0))
        self._on_policy_changed()

    # ------------------------------------------------------------------ Chọn file
    def pick_zip(self):
        if self._busy:
            return
        path = filedialog.askopenfilename(
            title="Chọn file ZIP cần giải nén",
            filetypes=[("ZIP Archive", "*.zip"), ("Tất cả file", "*.*")],
            parent=self.winfo_toplevel(),
        )
        if path:
            self.load_zip(path)

    def _browse_dest(self):
        init = self._dest_user_base or self._dest_base()
        while init and not Path(init).exists() and Path(init) != Path(init).parent:
            init = str(Path(init).parent)
        path = filedialog.askdirectory(
            title="Chọn thư mục giải nén", initialdir=init or None, parent=self.winfo_toplevel()
        )
        if path:
            self._dest_user_base = os.path.normpath(path)  # thư mục gốc người dùng chọn
            self._dest_dirty = False
            settings_service.set("last_extract_dir", self._dest_user_base)
            self._suggest_dest()
            self._validate()

    # ------------------------------------------------------------------ Nạp ZIP (luồng nền)
    def load_zip(self, file_path: str):
        p = Path(file_path).resolve()
        if not p.is_file():
            self._show_error("File không tồn tại", "Có thể file đã bị di chuyển hoặc xóa.")
            return
        self.zip_path = str(p)
        self.meta, self.entries = None, []
        self._loading = True
        self._load_token += 1
        token = self._load_token
        self._dest_dirty = False
        self._show_card_loading(p)
        self._refresh_layout()
        self._suggest_dest()
        self._validate()

        def worker():
            try:
                cap = float(settings_service.get("large_archive_threshold_gb", 10.0) or 10.0)
                meta = get_archive_metadata(p, max_bomb_uncompressed_bytes=int(cap * 1024**3))
                entries = list_archive_entries(p)
                self._load_q.put((token, meta, entries, None))
            except Exception as exc:  # noqa: BLE001 — hiển thị thân thiện, log đã ghi ở core
                self._load_q.put((token, None, None, exc))

        threading.Thread(target=worker, daemon=True).start()
        self.after(80, self._poll_load)

    def _poll_load(self):
        try:
            token, meta, entries, exc = self._load_q.get_nowait()
        except queue.Empty:
            if self._loading:
                self.after(80, self._poll_load)
            return
        if token != self._load_token:  # kết quả cũ (người dùng đã chọn file khác)
            self.after(80, self._poll_load)
            return
        self._loading = False
        if exc is not None:
            self.zip_path = None
            self._show_error("Không đọc được file ZIP", friendly_error(str(exc), type(exc).__name__))
            self._refresh_layout()
            self._validate()
            return
        self.meta, self.entries = meta, entries
        recent_service.add(self.zip_path)
        self._fill_card()
        self._refresh_layout()
        self._validate()
        if meta.is_encrypted:
            self.pwd_entry.focus_set()

    # ------------------------------------------------------------------ Thẻ xem trước
    def _clear_slot(self):
        for w in self.preview_slot.winfo_children():
            if w is not self.card:
                w.destroy()
        self.card.grid_forget()

    def _show_card_loading(self, p: Path):
        self._clear_slot()
        self.card.grid(row=0, column=0, sticky="ew")
        self.name_lbl.configure(text=shorten_middle(p.name, 48))
        self.meta_lbl.configure(text="Đang đọc archive...")
        for w in self.badges.winfo_children():
            w.destroy()
        self.warn_box.grid_forget()
        self.btn_toggle.configure(state="disabled")

    def _fill_card(self):
        m = self.meta
        self.btn_toggle.configure(state="normal")
        self.meta_lbl.configure(
            text=(
                f"{human_size(m.file_size)} • {format_count(m.total_files)} file • "
                f"{format_count(m.total_dirs)} thư mục • Nén {m.ratio_percent:.0f}%"
            )
        )
        for w in self.badges.winfo_children():
            w.destroy()
        if m.is_encrypted:
            StatusBadge(self.badges, "info", "Có mật khẩu", icon="lock").pack(side="left")

        msgs = []
        if settings_service.get("warn_large_archive", True):
            if m.has_zip_bomb_risk:
                msgs.append(m.zip_bomb_warning or "Tỷ lệ nén bất thường — hãy cẩn thận khi giải nén.")
            thr = float(settings_service.get("large_archive_threshold_gb", 10.0) or 10.0)
            if m.uncompressed_size > thr * 1024**3:
                msgs.append(
                    f"Dung lượng sau giải nén khoảng {human_size(m.uncompressed_size)}, lớn hơn ngưỡng cảnh báo {thr:g} GB."
                )
        if msgs:
            self.warn_lbl.configure(text=" " + "\n ".join(msgs))
            self.warn_box.grid(row=2, column=0, columnspan=3, sticky="ew", padx=SP12, pady=(0, SP12))
        else:
            self.warn_box.grid_forget()

    def _show_error(self, title: str, desc: str):
        self._clear_slot()
        EmptyState(
            self.preview_slot, title=title, description=desc, icon="warn",
            action_text="Chọn file ZIP khác", action=self.pick_zip,
        ).grid(row=0, column=0, sticky="ew")

    def _open_contents(self):
        """Mở cửa sổ riêng (co giãn được) thay vì ép danh sách vào màn hình chính."""
        if not self.entries:
            return
        if self._contents_win is not None and self._contents_win.winfo_exists():
            bring_to_front(self._contents_win, self.winfo_toplevel())
            return
        self._contents_win = ArchiveContentsWindow(
            self.winfo_toplevel(), Path(self.zip_path).name, self.entries
        )

    # ------------------------------------------------------------------ Bố cục theo trạng thái
    def _refresh_layout(self):
        loaded = self.zip_path is not None or self._has_error_slot()
        ready = self.zip_path is not None and not self._loading and self.meta is not None
        self.drop.set_compact(loaded)

        for w in (self.drop, self.preview_slot, self.pwd_row,
                  self.dest_holder, self.advanced, self.btn_start):
            w.pack_forget()

        # Phần đáy được pack trước => không bao giờ bị cắt khi cửa sổ nhỏ
        if self.zip_path:
            self.btn_start.pack(side="bottom", fill="x", pady=(SP12, 0))
            self.advanced.pack(side="bottom", fill="x", pady=(SP12, 0))
            self.dest_holder.pack(side="bottom", fill="x", pady=(SP12, 0))
            if ready and self.meta.is_encrypted:
                self.pwd_row.pack(side="bottom", fill="x", pady=(SP12, 0))

        if loaded:
            self.drop.pack(side="top", fill="x")
            self.preview_slot.pack(side="top", fill="x", pady=(SP12, 0))
        else:
            self.drop.pack(side="top", fill="both", expand=True)

    def _has_error_slot(self) -> bool:
        return any(w is not self.card for w in self.preview_slot.winfo_children())

    # ------------------------------------------------------------------ Đích giải nén
    def _dest_base(self) -> str:
        last = settings_service.get("last_extract_dir") or ""
        if last and Path(last).is_dir():
            return last
        return str(Path(self.zip_path).parent) if self.zip_path else str(Path.home())

    def _suggest_dest(self):
        if not self.zip_path or self._dest_dirty:
            return
        base = self._dest_user_base or self._dest_base()
        self.dest.set(os.path.normpath(suggest_extract_dir(self.zip_path, self.subfolder_var.get(), base)))

    def _on_dest_edited(self):
        self._dest_dirty = True
        self._validate()

    def _on_subfolder_toggle(self):
        if not self.zip_path:
            return
        stem = Path(self.zip_path).stem
        cur = Path(self.dest.get()) if self.dest.get() else None
        if self._dest_dirty and cur is not None:
            base = cur.parent if cur.name == stem else cur
            self.dest.set(str(base / stem if self.subfolder_var.get() else base))
        else:
            self._suggest_dest()
        self._validate()

    # ------------------------------------------------------------------ Mật khẩu / tùy chọn
    def _toggle_pwd(self):
        self._eye_visible = not self._eye_visible
        self.pwd_entry.configure(show="" if self._eye_visible else "•")
        self.btn_eye.set_icon("eye_off" if self._eye_visible else "eye")

    def _on_policy_changed(self):
        pol = OverwritePolicy(self.policy_var.get())
        if pol == OverwritePolicy.OVERWRITE:
            self.policy_warn.grid()
        else:
            self.policy_warn.grid_remove()
        self.advanced.set_summary(f"Khi trùng tên: {POLICY_SHORT[pol]}")

    # ------------------------------------------------------------------ Kiểm tra hợp lệ
    def _validate(self) -> bool:
        ok = self.zip_path is not None and self.meta is not None and not self._loading and not self._busy
        if self.zip_path:
            err, warn = validate_dest_dir(self.dest.get())
            if err:
                self.dest.set_message(err, "error")
                ok = False
            elif warn and self._dest_dirty:  # đề xuất tự động thì im lặng, chỉ báo khi người dùng tự gõ
                self.dest.set_message(warn, "warning")
            else:
                self.dest.clear_message()
        if self.meta is not None and self.meta.is_encrypted:
            if not self.pwd_entry.get():
                ok = False  # cần mật khẩu; placeholder của ô nhập đã nói rõ
        self.btn_start.configure(state="normal" if ok else "disabled")
        return ok

    # ------------------------------------------------------------------ Bắt đầu
    def start(self):
        self._on_click_start()

    def _on_click_start(self):
        if self._busy or not self._validate():
            return
        m = self.meta
        if m is not None and m.has_zip_bomb_risk and settings_service.get("warn_large_archive", True):
            if not messagebox.askyesno(
                "Archive có dấu hiệu bất thường",
                (m.zip_bomb_warning or "Tỷ lệ nén bất thường.") + "\n\nBạn vẫn muốn giải nén?",
                icon="warning",
                parent=self.winfo_toplevel(),
            ):
                return
        password = self.pwd_entry.get() or None
        self.on_start(self.zip_path, self.dest.get(), password, OverwritePolicy(self.policy_var.get()))

    def reset(self):
        """Sau khi hoàn tất và chọn 'Giải nén tiếp'."""
        self.zip_path, self.meta, self.entries = None, None, []
        self._dest_dirty = False
        self.pwd_entry.delete(0, "end")
        self._clear_slot()
        self._refresh_layout()
        self._validate()

    def set_busy(self, busy: bool):
        self._busy = busy
        self.drop.set_state("processing" if busy else "normal")
        self.btn_start.configure(state="disabled" if busy else "normal")
        if not busy:
            self._validate()
