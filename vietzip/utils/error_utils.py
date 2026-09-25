"""Chuyển lỗi kỹ thuật thành thông báo dễ hiểu cho người dùng phổ thông.

Log vẫn ghi đầy đủ ở core; hàm này chỉ dùng cho phần hiển thị.
"""

from __future__ import annotations

from typing import Optional

WRONG_PASSWORD_MSG = "Mật khẩu không đúng hoặc archive không hợp lệ."


def friendly_error(error: Optional[str], details: Optional[str] = None) -> str:
    """Trả về thông báo tiếng Việt có hướng xử lý. Không bao giờ trả về traceback."""
    raw = f"{error or ''} {details or ''}".lower()

    if not raw.strip():
        return "Có lỗi không xác định xảy ra. Hãy thử lại hoặc xem chi tiết."
    if "password" in raw or "mật khẩu" in raw or "encrypted" in raw:
        return WRONG_PASSWORD_MSG
    if "not a zip file" in raw or "badzipfile" in raw or "bad magic" in raw or "corrupt" in raw:
        return "File này không phải ZIP hợp lệ hoặc đã bị hỏng. Hãy thử tải/tạo lại file."
    if "crc" in raw:
        return "Kiểm tra CRC thất bại: dữ liệu trong file có thể đã bị hỏng."
    if "no space left" in raw or "errno 28" in raw or "disk full" in raw:
        return "Ổ đĩa đã đầy. Hãy giải phóng dung lượng hoặc chọn ổ đĩa khác rồi thử lại."
    if "permission denied" in raw or "permissionerror" in raw or "access is denied" in raw or "errno 13" in raw:
        return "Không có quyền ghi vào thư mục đích. Hãy chọn thư mục khác (ví dụ Documents)."
    if "read-only" in raw:
        return "Thư mục đích ở chế độ chỉ đọc. Hãy chọn thư mục khác."
    if "filenotfound" in raw or "no such file" in raw or "không tồn tại" in raw:
        return "Không tìm thấy file hoặc thư mục. Có thể nó đã bị di chuyển hoặc xóa."
    if "path too long" in raw or "filename too long" in raw or "errno 36" in raw:
        return "Đường dẫn quá dài. Hãy chọn thư mục đích ngắn hơn."
    return (error or "Có lỗi xảy ra").strip()
