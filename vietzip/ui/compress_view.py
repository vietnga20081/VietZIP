"""Màn hình Nén: kéo thả → danh sách → nơi lưu → tùy chọn nâng cao → Nén ngay."""

from __future__ import annotations

import os
import queue
import threading
from pathlib import Path
from tkinter import filedialog, messagebox
from typing import Callable, Optional

import customtkinter as ctk

from vietzip.core.compressor import HAS_PYZIPPER
from vietzip.core.models import COMPRESSION_LEVELS
from vietzip.services.settings_service import settings_service
from vietzip.ui.components import (
    AdvancedOptions,
    AppButton,
    DropZone,
    FileList,
    IconButton,
    OutputPicker,
    Tooltip,
)
from vietzip.ui.theme import (
    CHECKBOX_STYLE,
    COLOR_DANGER,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    COLOR_WARNING,
    ENTRY_STYLE,
    FONT_BUTTON_LG,
    FONT_SECTION,
    FONT_SMALL,
    RADIO_STYLE,
    SP4,
    SP8,
    SP12,
    SP16,
)
from vietzip.ui.widgets import get_logo_image
from vietzip.utils.format_utils import human_size
from vietzip.utils.path_utils import (
    normalize_zip_output,
    suggest_output_path,
    validate_output_zip,
)

# (nhãn, giá trị nén, mô tả). Giá trị phải nằm trong COMPRESSION_LEVELS của core.
LEVEL_CHOICES = [
    ("Siêu nhanh", 0, "gần như không nén"),
    ("Nhanh", 3, "ưu tiên tốc độ"),
    ("Cân bằng", 6, "khuyến nghị"),
    ("Nén tối đa", 9, "ưu tiên dung lượng"),
]
_LEVEL_VALUES = {v for v in COMPRESSION_LEVELS.values()}
assert all(v in _LEVEL_VALUES for _, v, _ in LEVEL_CHOICES)


class CompressView(ctk.CTkFrame):
    """Giao diện Nén. Không chứa logic nén — chỉ thu thập lựa chọn rồi gọi `on_start`."""

    def __init__(
        self,
        master,
        on_start: Callable[[list[str], str, int, Optional[str], bool], None],
        notify: Callable[[str, str, str], None],
        **kwargs,
    ):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.on_start = on_start
        self.notify = notify

        self.items: list[str] = []
        self._info: dict[str, dict] = {}
        self._pending_scans = 0
        self._scan_q: queue.Queue = queue.Queue()
        self._output_dirty = False  # người dùng đã tự sửa đường dẫn đầu ra
        self._busy = False

        self._build()
        self._refresh()

    # ------------------------------------------------------------------ Dựng UI
    def _build(self):
        self.drop = DropZone(
            self,
            on_pick_files=self.pick_files,
            on_pick_folder=self.pick_folder,
            mode="compress",
            logo_image=get_logo_image(64) if settings_service.get("show_mascot", True) else None,
        )
        self.file_list = FileList(self, on_remove=self.remove_item, on_clear=self.clear_all)
        self.output = OutputPicker(
            self,
            label="Lưu file ZIP tại",
            placeholder="Chọn nơi lưu file ZIP...",
            browse_text="Chọn...",
            on_browse=self._browse_output,
            on_edit=self._on_output_edited,
        )
        self.advanced = AdvancedOptions(self)
        self._build_advanced(self.advanced.body)
        self.btn_start = AppButton(
            self, text="Nén ngay", kind="primary", icon="archive", icon_size=20, height=48,
            font=FONT_BUTTON_LG, command=self._on_click_start,
        )
        self._laid_out_has: Optional[bool] = None

    def _layout(self, has: bool):
        """Nút chính + tùy chọn được pack trước (ở đáy) nên không bao giờ bị cắt; danh sách file co giãn."""
        if has == self._laid_out_has:
            return
        self._laid_out_has = has
        for w in (self.drop, self.file_list, self.output, self.advanced, self.btn_start):
            w.pack_forget()
        self.btn_start.pack(side="bottom", fill="x", pady=(SP12, 0))
        if has:
            self.advanced.pack(side="bottom", fill="x", pady=(SP12, 0))
            self.output.pack(side="bottom", fill="x", pady=(SP12, 0))
            self.drop.pack(side="top", fill="x")
            self.file_list.pack(side="top", fill="both", expand=True, pady=(SP12, 0))
        else:
            self.drop.pack(side="top", fill="both", expand=True)

    def _build_advanced(self, body):
        body.grid_columnconfigure((0, 1), weight=1)
        body.grid_columnconfigure(2, weight=0)

        ctk.CTkLabel(body, text="Mức nén", font=FONT_SECTION, text_color=COLOR_TEXT_PRIMARY, anchor="w").grid(
            row=0, column=0, columnspan=3, sticky="w", pady=(0, SP4)
        )
        default_lvl = settings_service.get("compression_level", 6)
        if default_lvl not in {v for _, v, _ in LEVEL_CHOICES}:
            default_lvl = 6
        self.level_var = ctk.IntVar(value=default_lvl)
        for i, (label, value, desc) in enumerate(LEVEL_CHOICES):
            ctk.CTkRadioButton(
                body, text=f"{label} — {desc}", variable=self.level_var, value=value,
                command=self._on_option_changed, **RADIO_STYLE,
            ).grid(row=1 + i // 2, column=i % 2, sticky="w", pady=2, padx=(0, SP16))

        ctk.CTkLabel(body, text="Mật khẩu (tùy chọn)", font=FONT_SECTION, text_color=COLOR_TEXT_PRIMARY, anchor="w").grid(
            row=3, column=0, columnspan=3, sticky="w", pady=(SP12, SP4)
        )
        self.pwd_entry = ctk.CTkEntry(body, placeholder_text="Để trống nếu không mã hóa", show="•", **ENTRY_STYLE)
        self.pwd_entry.grid(row=4, column=0, sticky="ew", padx=(0, SP8))
        self.pwd2_entry = ctk.CTkEntry(body, placeholder_text="Nhập lại mật khẩu", show="•", **ENTRY_STYLE)
        self.pwd2_entry.grid(row=4, column=1, sticky="ew", padx=(0, SP8))
        self.btn_eye = IconButton(body, icon="eye", tooltip="Hiện/ẩn mật khẩu", command=self._toggle_pwd, size=36)
        self.btn_eye.grid(row=4, column=2)
        self._eye_visible = False
        for e in (self.pwd_entry, self.pwd2_entry):
            e.bind("<KeyRelease>", lambda ev: self._on_option_changed(), add="+")

        self.pwd_msg = ctk.CTkLabel(body, text="", font=FONT_SMALL, anchor="w", justify="left")
        self.pwd_msg.grid(row=5, column=0, columnspan=3, sticky="w", pady=(SP4, 0))
        self.pwd_msg.grid_remove()

        self.verify_var = ctk.BooleanVar(value=settings_service.get("verify_archive", True))
        chk = ctk.CTkCheckBox(
            body, text="Xác minh file sau khi nén", variable=self.verify_var,
            command=self._on_option_changed, **CHECKBOX_STYLE,
        )
        chk.grid(row=6, column=0, columnspan=3, sticky="w", pady=(SP12, 0))
        Tooltip(chk, "Kiểm tra CRC từng file trong ZIP vừa tạo để chắc chắn dữ liệu không bị lỗi.\n"
                     "An toàn hơn nhưng tốn thêm một chút thời gian.")

        if not HAS_PYZIPPER:
            for e in (self.pwd_entry, self.pwd2_entry):
                e.configure(state="disabled")
            self._set_pwd_msg("Thiếu thư viện pyzipper nên chưa thể đặt mật khẩu (cài: pip install pyzipper).", "warn")

    # ------------------------------------------------------------------ Hành động chọn file
    def pick_files(self):
        if self._busy:
            return
        files = filedialog.askopenfilenames(title="Chọn file cần nén", parent=self.winfo_toplevel())
        if files:
            self.add_paths(list(files))

    def pick_folder(self):
        if self._busy:
            return
        folder = filedialog.askdirectory(title="Chọn thư mục cần nén", parent=self.winfo_toplevel())
        if folder:
            self.add_paths([folder])

    def _browse_output(self):
        current = self.output.get()
        init_dir = str(Path(current).parent) if current else self._base_dir()
        if not Path(init_dir).exists():
            init_dir = self._base_dir()
        name = Path(current).name if current else "Archive.zip"
        path = filedialog.asksaveasfilename(
            title="Lưu file ZIP", defaultextension=".zip", initialdir=init_dir, initialfile=name,
            filetypes=[("ZIP Archive", "*.zip")], parent=self.winfo_toplevel(), confirmoverwrite=False,
        )
        if path:
            self.output.set(os.path.normpath(path))
            self._output_dirty = True
            settings_service.set("last_output_dir", str(Path(path).parent))
            self._validate()

    # ------------------------------------------------------------------ Danh sách nguồn
    def add_paths(self, paths: list[str]) -> int:
        added = 0
        for p in paths:
            clean = os.path.normpath(p)
            if clean not in self.items and os.path.exists(clean):
                self.items.append(clean)
                self._start_scan(clean)
                added += 1
        if added:
            self._refresh()
        return added

    def remove_item(self, path: str):
        if self._busy:
            return
        if path in self.items:
            self.items.remove(path)
            self._info.pop(path, None)
            self._refresh()

    def clear_all(self):
        if self._busy:
            return
        self.items.clear()
        self._info.clear()
        self._output_dirty = False
        self._refresh()

    def reset(self):
        """Dùng sau khi hoàn tất và người dùng chọn 'Nén tiếp'."""
        self.clear_all()
        for e in (self.pwd_entry, self.pwd2_entry):
            e.delete(0, "end")
        self._on_option_changed()

    # ------------------------------------------------------------------ Quét dung lượng (nền)
    def _start_scan(self, path: str):
        self._pending_scans += 1

        def worker():
            info = {"is_dir": os.path.isdir(path), "size": 0, "files": 0}
            try:
                if info["is_dir"]:
                    for root, _dirs, files in os.walk(path):
                        for f in files:
                            info["files"] += 1
                            try:
                                info["size"] += os.stat(os.path.join(root, f)).st_size
                            except OSError:
                                pass
                else:
                    info["size"] = os.stat(path).st_size
                    info["files"] = 1
            except OSError:
                pass
            self._scan_q.put((path, info))

        threading.Thread(target=worker, daemon=True).start()
        self.after(120, self._poll_scan)

    def _poll_scan(self):
        changed = False
        try:
            while True:
                path, info = self._scan_q.get_nowait()
                self._pending_scans = max(0, self._pending_scans - 1)
                if path in self.items:
                    self._info[path] = info
                    changed = True
        except queue.Empty:
            pass
        if changed:
            self._refresh(rebuild_output=False)
        if self._pending_scans > 0:
            self.after(150, self._poll_scan)

    # ------------------------------------------------------------------ Cập nhật giao diện
    def _base_dir(self) -> str:
        d = settings_service.get("default_output_dir") or ""
        if d and Path(d).is_dir():
            return d
        last = settings_service.get("last_output_dir") or ""
        if last and Path(last).is_dir():
            return last
        return str(Path(self.items[0]).parent) if self.items else str(Path.home())

    def _refresh(self, rebuild_output: bool = True):
        has = bool(self.items)
        self.drop.set_compact(has)
        self._layout(has)

        rows = []
        total = 0
        for p in self.items:
            info = self._info.get(p)
            rows.append({"path": p, "is_dir": os.path.isdir(p), "size": info["size"] if info else None})
            total += info["size"] if info else 0
        summary = f"{len(self.items)} mục • {human_size(total)}"
        if self._pending_scans:
            summary += " • đang tính..."
        self.file_list.render(rows, summary)

        if has and rebuild_output and not self._output_dirty:
            self.output.set(
                suggest_output_path(
                    self.items, self._base_dir(), settings_service.get("filename_behavior", "smart")
                )
            )
        self._on_option_changed()
        self._validate()

    def _on_output_edited(self):
        self._output_dirty = True
        self._validate()

    def _toggle_pwd(self):
        self._eye_visible = not self._eye_visible
        show = "" if self._eye_visible else "•"
        for e in (self.pwd_entry, self.pwd2_entry):
            e.configure(show=show)
        self.btn_eye.set_icon("eye_off" if self._eye_visible else "eye")

    def _set_pwd_msg(self, text: str, kind: str = "muted"):
        color = {"error": COLOR_DANGER, "warn": COLOR_WARNING}.get(kind, COLOR_TEXT_MUTED)
        self.pwd_msg.configure(text=text, text_color=color)
        if text:
            self.pwd_msg.grid()
        else:
            self.pwd_msg.grid_remove()

    def _on_option_changed(self):
        pwd = self.pwd_entry.get()
        pwd2 = self.pwd2_entry.get()
        if HAS_PYZIPPER:
            if pwd and pwd2 and pwd != pwd2:
                self._set_pwd_msg("Mật khẩu nhập lại chưa khớp.", "error")
            elif pwd:
                self._set_pwd_msg("Mã hóa AES-256. Hãy ghi nhớ mật khẩu — VietZIP không thể khôi phục.")
            else:
                self._set_pwd_msg("")
        # tóm tắt khi thu gọn
        level_name = next((l for l, v, _ in LEVEL_CHOICES if v == self.level_var.get()), "Cân bằng")
        parts = [level_name]
        if pwd:
            parts.append("Có mật khẩu")
        if self.verify_var.get():
            parts.append("Xác minh")
        self.advanced.set_summary(" · ".join(parts))
        self._validate()

    # ------------------------------------------------------------------ Kiểm tra hợp lệ
    def _validate(self) -> bool:
        ok = bool(self.items) and not self._busy
        if self.items:
            err, warn = validate_output_zip(self.output.get(), self.items)
            if err:
                self.output.set_message(err, "error")
                ok = False
            elif warn:
                self.output.set_message(warn, "warning")
            else:
                self.output.clear_message()
        if HAS_PYZIPPER:
            pwd, pwd2 = self.pwd_entry.get(), self.pwd2_entry.get()
            if pwd and pwd != pwd2:
                ok = False
        self.btn_start.configure(state="normal" if ok else "disabled")
        return ok

    # ------------------------------------------------------------------ Bắt đầu
    def start(self):
        """Gọi từ phím Enter / nút chính."""
        self._on_click_start()

    def _on_click_start(self):
        if self._busy or not self._validate():
            return
        output = normalize_zip_output(self.output.get())
        if Path(output).exists():
            if not messagebox.askyesno(
                "File đã tồn tại",
                f"'{Path(output).name}' đã có sẵn.\nBạn có muốn ghi đè không?",
                icon="warning",
                parent=self.winfo_toplevel(),
            ):
                return
        password = self.pwd_entry.get() or None  # không strip: khoảng trắng có thể là một phần mật khẩu
        self.on_start(list(self.items), output, self.level_var.get(), password, self.verify_var.get())

    def set_busy(self, busy: bool):
        self._busy = busy
        self.drop.set_state("processing" if busy else "normal")
        self.file_list.set_busy(busy)
        self.btn_start.configure(state="disabled" if busy else "normal")
        if not busy:
            self._validate()
