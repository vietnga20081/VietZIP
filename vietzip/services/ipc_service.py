"""Inter-process communication (IPC) for single-instance application management.

Prevents multiple VietZIP instances when selecting multiple files in Windows Explorer,
and routes additional files to the currently running primary window.
"""

from __future__ import annotations

import json
import os
import socket
import sys
import threading
import time
from pathlib import Path
from typing import Callable, Optional

from vietzip.utils.logging_utils import logger

VIETZIP_IPC_PORT = 48729
IPC_MAGIC = "VIETZIP_IPC_v1"


class WindowsMutex:
    """Named Mutex ở cấp độ Windows Kernel để xác định Primary Instance tức thì không có race condition."""

    MUTEX_NAME = "Local\\VietZIP_SingleInstance_Mutex"

    def __init__(self):
        self.handle = None
        self.is_primary = False

    def acquire(self) -> bool:
        """
        Thử tạo Named Mutex trong Windows Kernel.
        Trả về True nếu đây là Primary Instance (tiến trình tạo mutex thành công).
        Trả về False nếu mutex đã tồn tại (ERROR_ALREADY_EXISTS = 183).
        """
        if sys.platform != "win32":
            self.is_primary = True
            return True

        import ctypes
        from ctypes import wintypes

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        CreateMutexW = kernel32.CreateMutexW
        CreateMutexW.argtypes = [wintypes.LPVOID, wintypes.BOOL, wintypes.LPCWSTR]
        CreateMutexW.restype = wintypes.HANDLE

        self.handle = CreateMutexW(None, False, self.MUTEX_NAME)
        err = ctypes.get_last_error()
        if err == 183:  # ERROR_ALREADY_EXISTS
            self.is_primary = False
            return False

        self.is_primary = bool(self.handle)
        return self.is_primary

    def release(self):
        if self.handle and sys.platform == "win32":
            import ctypes
            from ctypes import wintypes

            kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
            kernel32.CloseHandle(self.handle)
            self.handle = None


def normalize_input_path(raw_path: str) -> str:
    """
    Làm sạch và chuẩn hóa đường dẫn từ tham số dòng lệnh Windows.
    Xử lý lỗi kinh điển của Windows C-runtime khi thư mục có trailing backslash (\")
    làm ký tự quote bị escape thành ký tự chuỗi thông thường.
    """
    if not raw_path:
        return ""

    p = raw_path.strip().strip('"').strip("'")
    if p.endswith('\\"') or p.endswith('"'):
        p = p.rstrip('"')
    if p.endswith('\\') and not (len(p) == 3 and p[1:3] == ':\\'):
        p = p.rstrip('\\')

    try:
        norm = os.path.normpath(p)
        return norm
    except Exception:
        return p


def send_to_primary_instance(
    action: str, paths: list[str], timeout: float = 0.8
) -> bool:
    """
    Thử kết nối đến primary instance đang chạy trên cổng IPC localhost.
    Trả về True nếu gửi thành công và nhận được phản hồi OK.
    """
    clean_paths = []
    if paths:
        for p in paths:
            cp = normalize_input_path(p)
            if cp and os.path.exists(cp):
                clean_paths.append(cp)

    if not clean_paths and action != "focus":
        return False

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        sock.connect(("127.0.0.1", VIETZIP_IPC_PORT))
        payload = (
            json.dumps(
                {
                    "magic": IPC_MAGIC,
                    "action": action,
                    "paths": clean_paths,
                },
                ensure_ascii=False,
            )
            + "\n"
        )
        sock.sendall(payload.encode("utf-8"))

        resp_data = sock.recv(1024)
        if resp_data:
            resp = json.loads(resp_data.decode("utf-8").strip())
            if resp.get("status") == "ok":
                return True
        return False
    except Exception:
        return False
    finally:
        try:
            sock.close()
        except Exception:
            pass


class SingleInstanceServer:
    """Lắng nghe các tiến trình phụ gửi file tới và chuyển vào cửa sổ chính."""

    def __init__(self, on_receive: Optional[Callable[[str, list[str]], None]] = None):
        self.on_receive = on_receive
        self._pending_messages: list[tuple[str, list[str]]] = []
        self._lock = threading.Lock()
        self.server_socket: Optional[socket.socket] = None
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def set_callback(self, callback: Callable[[str, list[str]], None]):
        """Thiết lập callback sau khi MainWindow khởi tạo xong và flush tin nhắn tồn đọng."""
        with self._lock:
            self.on_receive = callback
            pending = list(self._pending_messages)
            self._pending_messages.clear()

        for action, paths in pending:
            try:
                callback(action, paths)
            except Exception as exc:
                logger.debug("Lỗi khi chuyển tiếp file nhận được qua IPC: %s", exc)

    def start(self) -> bool:
        """Thử bind cổng IPC. Trả về True nếu thành công trở thành Primary Server."""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(("127.0.0.1", VIETZIP_IPC_PORT))
            self.server_socket.listen(16)
            self.server_socket.settimeout(1.0)
            self._running = True
            self._thread = threading.Thread(target=self._listen_loop, daemon=True)
            self._thread.start()
            logger.info("Đã khởi chạy IPC Single-Instance Server trên cổng %d.", VIETZIP_IPC_PORT)
            return True
        except Exception as exc:
            logger.debug("Không thể khởi tạo IPC Server (có thể instance khác đã chiếm cổng): %s", exc)
            if self.server_socket:
                try:
                    self.server_socket.close()
                except Exception:
                    pass
                self.server_socket = None
            return False

    def _listen_loop(self):
        while self._running:
            try:
                client_sock, _ = self.server_socket.accept()
            except socket.timeout:
                continue
            except Exception:
                if self._running:
                    continue
                break

            # Xử lý kết nối từ client
            try:
                client_sock.settimeout(2.0)
                buffer = b""
                while not buffer.endswith(b"\n"):
                    chunk = client_sock.recv(4096)
                    if not chunk:
                        break
                    buffer += chunk

                if buffer:
                    line = buffer.decode("utf-8").strip()
                    data = json.loads(line)
                    if data.get("magic") == IPC_MAGIC:
                        action = data.get("action", "compress")
                        paths = data.get("paths", [])
                        client_sock.sendall(b'{"status":"ok"}\n')

                        with self._lock:
                            if self.on_receive:
                                self.on_receive(action, paths)
                            else:
                                self._pending_messages.append((action, paths))
                    else:
                        client_sock.sendall(b'{"status":"bad_magic"}\n')
            except Exception as exc:
                logger.debug("Lỗi nhận dữ liệu IPC: %s", exc)
            finally:
                try:
                    client_sock.close()
                except Exception:
                    pass

    def stop(self):
        """Dừng server socket."""
        self._running = False
        if self.server_socket:
            try:
                self.server_socket.close()
            except Exception:
                pass
            self.server_socket = None
