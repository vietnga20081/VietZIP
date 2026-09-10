import os
import sys
import time
from pathlib import Path
from typing import Optional

from vietzip.services.context_menu_service import (
    register_context_menu,
    unregister_context_menu,
)
from vietzip.services.ipc_service import (
    SingleInstanceServer,
    WindowsMutex,
    normalize_input_path,
    send_to_primary_instance,
)
from vietzip.ui.main_window import MainWindow
from vietzip.utils.logging_utils import logger


def run_app(argv: Optional[list[str]] = None):
    """Khởi động ứng dụng VietZIP kèm phân tích đối số dòng lệnh và IPC single-instance."""
    if argv is None:
        argv = sys.argv[1:]

    # Xử lý các lệnh CLI đặc biệt
    if "--register-context-menu" in argv:
        ok, msg = register_context_menu()
        print(f"[VietZIP] {msg}")
        return

    if "--unregister-context-menu" in argv:
        ok, msg = unregister_context_menu()
        print(f"[VietZIP] {msg}")
        return

    # Phân tích hành động từ menu chuột phải
    initial_action: Optional[str] = None
    raw_paths: list[str] = []

    if argv:
        first_arg = argv[0].lower()
        if first_arg == "compress":
            initial_action = "compress"
            raw_paths = argv[1:]
        elif first_arg == "extract":
            initial_action = "extract"
            raw_paths = argv[1:]
        else:
            raw_paths = argv

    initial_paths: list[str] = []
    for rp in raw_paths:
        cleaned = normalize_input_path(rp)
        if cleaned and os.path.exists(cleaned):
            initial_paths.append(cleaned)

    # 1. ATOMIC MUTEX CHECK (Tránh race condition khi chọn nhiều file trong Windows Explorer)
    mutex = WindowsMutex()
    is_primary = mutex.acquire()

    if not is_primary:
        # Đây là tiến trình phụ: gửi file tới Primary Instance rồi thoát ngay
        logger.info("Phát hiện Primary Instance đang chạy. Đang chuyển giao tác vụ qua IPC...")
        target_action = initial_action or ("compress" if initial_paths else "focus")

        for _ in range(30):
            if send_to_primary_instance(target_action, initial_paths, timeout=0.5):
                logger.info("Đã chuyển giao thành công cho Primary Instance. Thoát tiến trình phụ.")
                mutex.release()
                return
            time.sleep(0.05)

        logger.warning("Không kết nối được IPC tới Primary Instance sau 1.5s. Khởi động phiên độc lập.")

    # 2. ĐÂY LÀ TIẾN TRÌNH CHÍNH (Primary Instance):
    # Khởi chạy IPC Server NGAY LẬP TỨC để các tiến trình phụ gửi file tới có thể kết nối ngay
    ipc_server = SingleInstanceServer()
    ipc_server.start()

    logger.info("Khởi động giao diện chính VietZIP 2.0 (action=%s, paths=%s)...", initial_action, initial_paths)

    try:
        app = MainWindow(
            initial_action=initial_action,
            initial_paths=initial_paths,
        )

        # Gắn callback và giải phóng các file nhận được trong lúc MainWindow đang nạp
        ipc_server.set_callback(app.on_ipc_received)

        try:
            app.mainloop()
        finally:
            ipc_server.stop()
            mutex.release()

    except Exception as exc:
        logger.critical("Ngoại lệ nghiêm trọng không xử lý: %s", exc, exc_info=True)
        ipc_server.stop()
        mutex.release()
        try:
            from tkinter import messagebox
            messagebox.showerror(
                "Lỗi nghiêm trọng — VietZIP",
                f"Ứng dụng gặp sự cố không mong muốn:\n\n{exc}\n\nXem file logs/vietzip.log để biết chi tiết.",
            )
        except Exception:
            pass
        sys.exit(1)


if __name__ == "__main__":
    run_app()
