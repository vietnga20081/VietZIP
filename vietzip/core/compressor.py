"""Zip compression engine supporting progress tracking, cancellation, temp files, and AES password."""

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

from vietzip.core.models import OperationResult, ProgressInfo
from vietzip.core.progress import ProgressTracker
from vietzip.utils.file_utils import collect_items_to_compress
from vietzip.utils.logging_utils import logger


def compress_archive(
    sources: Iterable[Path | str],
    output_path: Path | str,
    level: int = 6,
    password: Optional[str] = None,
    verify: bool = True,
    cancel_event: Optional[threading.Event] = None,
    progress_callback: Optional[Callable[[ProgressInfo], None]] = None,
    chunk_size: int = 1024 * 1024,  # 1 MB chunk
) -> OperationResult:
    """
    Nén danh sách file/thư mục thành file ZIP.
    - Ghi vào file tạm (.tmp) trước, rename nguyên tử khi hoàn tất.
    - Hỗ trợ cancel_event ngắt ngay lập tức và dọn dẹp file tạm.
    - Hỗ trợ mật khẩu AES-256 (nếu pyzipper khả dụng).
    - Tính toán tiến độ bytes chính xác, tốc độ và ETA.
    """
    start_time = time.time()
    out_path = Path(output_path).resolve()
    temp_path = out_path.with_name(out_path.name + ".tmp")

    # Đảm bảo thư mục cha tồn tại
    temp_path.parent.mkdir(parents=True, exist_ok=True)

    entries, total_bytes, total_files, total_dirs = collect_items_to_compress(sources)

    if not entries and total_files == 0 and total_dirs == 0:
        return OperationResult(
            success=False,
            operation="compress",
            error="Không có file hoặc thư mục hợp lệ nào để nén.",
        )

    tracker = ProgressTracker("Nén", total_files=total_files + total_dirs, total_bytes=total_bytes)
    warnings: list[str] = []
    processed_count = 0
    zf = None

    use_aes = bool(password and HAS_PYZIPPER)
    zip_class = pyzipper.AESZipFile if use_aes else zipfile.ZipFile
    zip_kwargs: dict = {
        "mode": "w",
        "compression": zipfile.ZIP_DEFLATED if level > 0 else zipfile.ZIP_STORED,
        "compresslevel": level,
        "allowZip64": True,
    }
    if use_aes:
        zip_kwargs["encryption"] = pyzipper.WZ_AES

    try:
        zf = zip_class(temp_path, **zip_kwargs)
        if password:
            zf.setpassword(password.encode("utf-8"))

        for full_path, arcname, file_size in entries:
            if cancel_event and cancel_event.is_set():
                logger.info("Tác vụ nén đã bị hủy bởi người dùng.")
                zf.close()
                zf = None
                if temp_path.exists():
                    temp_path.unlink(missing_ok=True)
                return OperationResult(
                    success=False,
                    operation="compress",
                    elapsed_seconds=time.time() - start_time,
                    cancelled=True,
                )

            processed_count += 1
            arcname_str = str(arcname).replace("\\", "/")

            if full_path.is_dir():
                # Thư mục (đặc biệt là thư mục rỗng)
                zinfo = zipfile.ZipInfo(filename=arcname_str.rstrip("/") + "/")
                zinfo.external_attr = 0o40775 << 16  # drwxrwxr-x
                zf.writestr(zinfo, "")
                info = tracker.update(0, arcname_str, processed_count)
                if progress_callback:
                    progress_callback(info)
                continue

            # File thông thường: đọc và ghi theo từng chunk để cập nhật mượt & phản hồi cancel
            try:
                with open(full_path, "rb") as src_fp, zf.open(
                    arcname_str, "w", force_zip64=True
                ) as dst_fp:
                    while True:
                        if cancel_event and cancel_event.is_set():
                            logger.info("Tác vụ nén đã bị hủy giữa chừng.")
                            zf.close()
                            zf = None
                            if temp_path.exists():
                                temp_path.unlink(missing_ok=True)
                            return OperationResult(
                                success=False,
                                operation="compress",
                                elapsed_seconds=time.time() - start_time,
                                cancelled=True,
                            )

                        chunk = src_fp.read(chunk_size)
                        if not chunk:
                            break
                        dst_fp.write(chunk)
                        info = tracker.update(len(chunk), arcname_str, processed_count)
                        if progress_callback:
                            progress_callback(info)

            except (PermissionError, FileNotFoundError, OSError) as read_err:
                msg = f"Không thể đọc file {full_path.name}: {read_err}"
                logger.warning(msg)
                warnings.append(msg)
                continue

        # Kiểm tra tính toàn vẹn (Verify archive CRC) nếu được yêu cầu
        if verify and zf is not None:
            first_bad = zf.testzip()
            if first_bad is not None:
                raise zipfile.BadZipFile(f"Kiểm tra CRC thất bại tại file: {first_bad}")

        zf.close()
        zf = None

        # Hoàn tất thành công: đổi tên file tạm sang output chính thức
        if out_path.exists():
            out_path.unlink(missing_ok=True)
        os.replace(temp_path, out_path)

        compressed_size = out_path.stat().st_size
        elapsed = time.time() - start_time

        logger.info(
            "Nén thành công %s: %d files, %d bytes -> %d bytes trong %.2fs",
            out_path.name,
            total_files,
            total_bytes,
            compressed_size,
            elapsed,
        )

        return OperationResult(
            success=True,
            operation="compress",
            output_path=str(out_path),
            file_count=total_files + total_dirs,
            original_size=total_bytes,
            compressed_size=compressed_size,
            elapsed_seconds=elapsed,
            warnings=warnings,
        )

    except Exception as exc:
        logger.exception("Lỗi trong quá trình nén: %s", exc)
        if zf is not None:
            try:
                zf.close()
            except Exception:
                pass
        if temp_path.exists():
            try:
                temp_path.unlink(missing_ok=True)
            except Exception:
                pass

        return OperationResult(
            success=False,
            operation="compress",
            elapsed_seconds=time.time() - start_time,
            error=str(exc),
            error_details=f"Lỗi khi nén: {type(exc).__name__} - {exc}",
            warnings=warnings,
        )
