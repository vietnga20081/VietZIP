"""Zip extraction engine supporting security checks, overwrite policy, progress, and cancellation."""

from __future__ import annotations

import os
import time
import zipfile
import threading
from pathlib import Path
from typing import Callable, Iterable, Optional

try:
    import pyzipper
    HAS_PYZIPPER = True
except ImportError:
    HAS_PYZIPPER = False

from vietzip.core.models import OperationResult, OverwritePolicy, ProgressInfo
from vietzip.core.progress import ProgressTracker
from vietzip.core.security import safe_extract_path, SecurityError
from vietzip.utils.file_utils import generate_unique_dest_path, get_available_disk_space
from vietzip.utils.logging_utils import logger


def extract_archive(
    zip_path: Path | str,
    dest_dir: Path | str,
    password: Optional[str] = None,
    overwrite_policy: OverwritePolicy = OverwritePolicy.AUTO_RENAME,
    on_overwrite_conflict: Optional[
        Callable[[Path], tuple[OverwritePolicy, bool]]
    ] = None,
    cancel_event: Optional[threading.Event] = None,
    progress_callback: Optional[Callable[[ProgressInfo], None]] = None,
    chunk_size: int = 1024 * 1024,
    members: Optional[Iterable[str]] = None,
) -> OperationResult:
    """
    Giải nén file ZIP vào thư mục đích.
    - Chống Zip Slip / Path Traversal bằng safe_extract_path.
    - Áp dụng OverwritePolicy (Ghi đè, Bỏ qua, Tự động đổi tên) hoặc hỏi qua callback.
    - Kiểm tra dung lượng đĩa khả dụng.
    - Hỗ trợ cancel_event dừng giữa chừng.
    - Hỗ trợ mật khẩu (cả ZipCrypto và AES).
    - `members`: nếu truyền vào (danh sách tên entry theo đúng `ArchiveEntry.filename`),
      chỉ giải nén các entry này thay vì toàn bộ archive. Thư mục cha của các file được
      chọn vẫn được tạo tự động dù entry thư mục đó không có trong danh sách.
    """
    start_time = time.time()
    source_zip = Path(zip_path).resolve()
    target_dir = Path(dest_dir).resolve()

    if not source_zip.exists():
        return OperationResult(
            success=False,
            operation="extract",
            error=f"File ZIP không tồn tại: {source_zip}",
        )

    target_dir.mkdir(parents=True, exist_ok=True)

    # Dùng pyzipper.AESZipFile nếu có để hỗ trợ cả AES và zip thông thường
    opener = pyzipper.AESZipFile if HAS_PYZIPPER else zipfile.ZipFile
    warnings: list[str] = []

    try:
        with opener(source_zip, "r") as zf:
            if password:
                zf.setpassword(password.encode("utf-8"))

            infolist = zf.infolist()
            if members is not None:
                wanted = set(members)
                infolist = [info for info in infolist if info.filename in wanted]
                if not infolist:
                    return OperationResult(
                        success=False,
                        operation="extract",
                        error="Không tìm thấy mục nào khớp với lựa chọn trong archive.",
                        elapsed_seconds=time.time() - start_time,
                    )
            total_bytes = sum(info.file_size for info in infolist)
            total_items = len(infolist)

            # Kiểm tra dung lượng đĩa trống
            free_space = get_available_disk_space(target_dir)
            if free_space > 0 and free_space < total_bytes:
                warnings.append(
                    f"Dung lượng đĩa khả dụng ({free_space // (1024**2)} MB) "
                    f"có thể không đủ cho archive ({total_bytes // (1024**2)} MB)."
                )

            tracker = ProgressTracker("Giải nén", total_files=total_items, total_bytes=total_bytes)
            current_policy = overwrite_policy
            apply_to_all = False

            extracted_count = 0

            for index, member in enumerate(infolist, start=1):
                if cancel_event and cancel_event.is_set():
                    logger.info("Tác vụ giải nén đã bị hủy bởi người dùng.")
                    return OperationResult(
                        success=False,
                        operation="extract",
                        elapsed_seconds=time.time() - start_time,
                        cancelled=True,
                    )

                # Kiểm tra an toàn đường dẫn
                try:
                    target_file = safe_extract_path(target_dir, member.filename)
                except SecurityError as sec_err:
                    logger.error("Bảo mật: Từ chối giải nén mục nguy hiểm: %s", sec_err)
                    warnings.append(str(sec_err))
                    continue

                # Nếu là thư mục
                is_dir = member.filename.endswith("/") or bool((member.external_attr >> 16) & 0o40000)
                if is_dir:
                    target_file.mkdir(parents=True, exist_ok=True)
                    info = tracker.update(0, member.filename, index)
                    if progress_callback:
                        progress_callback(info)
                    continue

                # Đảm bảo thư mục cha tồn tại
                target_file.parent.mkdir(parents=True, exist_ok=True)

                # Xử lý khi file đã tồn tại
                if target_file.exists():
                    policy = current_policy
                    if not apply_to_all and on_overwrite_conflict:
                        policy, apply_to_all = on_overwrite_conflict(target_file)
                        current_policy = policy

                    if policy == OverwritePolicy.SKIP:
                        logger.info("Bỏ qua file đã tồn tại: %s", target_file.name)
                        info = tracker.update(member.file_size, member.filename, index)
                        if progress_callback:
                            progress_callback(info)
                        continue
                    elif policy == OverwritePolicy.AUTO_RENAME:
                        target_file = generate_unique_dest_path(target_file)
                    # Nếu OVERWRITE thì tiếp tục ghi đè

                # Đọc và ghi từng chunk để cập nhật mượt và bắt cancel
                cancelled_mid_file = False
                try:
                    with zf.open(member, "r") as src_stream, open(
                        target_file, "wb"
                    ) as dst_stream:
                        while True:
                            if cancel_event and cancel_event.is_set():
                                cancelled_mid_file = True  # thoát `with` để đóng file rồi mới xóa file dở
                                break

                            chunk = src_stream.read(chunk_size)
                            if not chunk:
                                break
                            dst_stream.write(chunk)
                            info = tracker.update(len(chunk), member.filename, index)
                            if progress_callback:
                                progress_callback(info)

                    if cancelled_mid_file:
                        logger.info("Tác vụ giải nén đã bị hủy giữa chừng.")
                        target_file.unlink(missing_ok=True)  # không để lại file ghi dở
                        return OperationResult(
                            success=False,
                            operation="extract",
                            elapsed_seconds=time.time() - start_time,
                            cancelled=True,
                        )

                    # Phục hồi timestamp nếu có
                    if member.date_time:
                        try:
                            mtime = time.mktime(member.date_time + (0, 0, -1))
                            os.utime(target_file, (mtime, mtime))
                        except Exception:
                            pass

                    extracted_count += 1

                except (zipfile.BadZipFile, RuntimeError) as read_err:
                    # RuntimeError thường xảy ra khi sai mật khẩu trong zipfile
                    err_msg = str(read_err)
                    if "password" in err_msg.lower() or "bad password" in err_msg.lower() or "crc" in err_msg.lower():
                        raise RuntimeError("Mật khẩu không chính xác hoặc file bị hỏng.") from read_err
                    raise

                except OSError as os_err:
                    msg = f"Lỗi ghi file {target_file.name}: {os_err}"
                    logger.warning(msg)
                    warnings.append(msg)
                    continue

        elapsed = time.time() - start_time
        logger.info(
            "Giải nén thành công %s vào %s (%d mục) trong %.2fs",
            source_zip.name,
            target_dir,
            extracted_count,
            elapsed,
        )

        return OperationResult(
            success=True,
            operation="extract",
            output_path=str(target_dir),
            file_count=extracted_count,
            original_size=source_zip.stat().st_size,
            compressed_size=total_bytes,
            elapsed_seconds=elapsed,
            warnings=warnings,
        )

    except Exception as exc:
        logger.exception("Lỗi khi giải nén file ZIP: %s", exc)
        return OperationResult(
            success=False,
            operation="extract",
            elapsed_seconds=time.time() - start_time,
            error=str(exc),
            error_details=f"Lỗi giải nén: {type(exc).__name__} - {exc}",
            warnings=warnings,
        )


def extract_selected(
    zip_path: Path | str,
    dest_dir: Path | str,
    members: Iterable[str],
    password: Optional[str] = None,
    overwrite_policy: OverwritePolicy = OverwritePolicy.AUTO_RENAME,
    on_overwrite_conflict: Optional[
        Callable[[Path], tuple[OverwritePolicy, bool]]
    ] = None,
    cancel_event: Optional[threading.Event] = None,
    progress_callback: Optional[Callable[[ProgressInfo], None]] = None,
    chunk_size: int = 1024 * 1024,
) -> OperationResult:
    """Giải nén CHỈ các entry trong `members` (theo `ArchiveEntry.filename`).

    Lớp mỏng bọc `extract_archive(..., members=...)` để lời gọi tại nơi khác trong
    codebase (UI) đọc được ngay ý định mà không cần biết tham số `members` là gì.
    """
    return extract_archive(
        zip_path=zip_path,
        dest_dir=dest_dir,
        password=password,
        overwrite_policy=overwrite_policy,
        on_overwrite_conflict=on_overwrite_conflict,
        cancel_event=cancel_event,
        progress_callback=progress_callback,
        chunk_size=chunk_size,
        members=members,
    )
