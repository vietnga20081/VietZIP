"""Logging utilities for VietZIP."""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logging(log_dir: Path | str | None = None) -> logging.Logger:
    """Khởi tạo hệ thống log ghi vào logs/vietzip.log và console."""
    if log_dir is None:
        log_dir = Path("logs")
    else:
        log_dir = Path(log_dir)

    try:
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / "vietzip.log"
    except Exception:
        log_file = None

    logger = logging.getLogger("vietzip")
    logger.setLevel(logging.DEBUG)

    # Tránh gắn handler lặp lại nếu đã cấu hình
    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File Handler (5 MB max, giữ lại 3 backup files)
    if log_file:
        try:
            file_handler = RotatingFileHandler(
                log_file, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
            )
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as exc:
            logger.warning("Không thể khởi tạo file log: %s", exc)

    return logger


logger = setup_logging()
