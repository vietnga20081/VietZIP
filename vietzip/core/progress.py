"""Accurate progress tracking, speed smoothing, and ETA calculation."""

from __future__ import annotations

import time
from typing import Optional

from vietzip.core.models import ProgressInfo


class ProgressTracker:
    """
    Theo dõi tiến trình theo bytes, tính tốc độ (EMA smoothing) và dự đoán thời gian (ETA).
    """

    def __init__(
        self,
        operation: str,
        total_files: int,
        total_bytes: int,
        smoothing_factor: float = 0.25,
    ):
        self.operation = operation
        self.total_files = max(total_files, 1)
        self.total_bytes = total_bytes
        self.smoothing_factor = smoothing_factor

        self.processed_bytes = 0
        self.current_file = ""
        self.current_index = 0

        self.start_time = time.time()
        self.last_update_time = self.start_time
        self.last_processed_bytes = 0
        self.smoothed_speed = 0.0

    def update(
        self,
        bytes_added: int,
        current_file: str,
        current_index: int,
    ) -> ProgressInfo:
        """Cập nhật lượng byte vừa xử lý và tính toán tốc độ/ETA."""
        now = time.time()
        self.processed_bytes += bytes_added
        self.current_file = current_file
        self.current_index = current_index

        dt = now - self.last_update_time
        # Cập nhật tốc độ mỗi 0.1s trở lên để tránh chia cho dt quá nhỏ
        if dt >= 0.1:
            delta_bytes = self.processed_bytes - self.last_processed_bytes
            instant_speed = delta_bytes / dt

            if self.smoothed_speed == 0.0:
                self.smoothed_speed = instant_speed
            else:
                self.smoothed_speed = (
                    self.smoothing_factor * instant_speed
                    + (1.0 - self.smoothing_factor) * self.smoothed_speed
                )

            self.last_update_time = now
            self.last_processed_bytes = self.processed_bytes

        # Tính tỷ lệ %
        if self.total_bytes > 0:
            percent = min(1.0, max(0.0, self.processed_bytes / self.total_bytes))
        else:
            percent = min(1.0, max(0.0, self.current_index / self.total_files))

        # Tính ETA
        eta: Optional[float] = None
        if self.smoothed_speed > 1024 and self.total_bytes > self.processed_bytes:
            remaining_bytes = self.total_bytes - self.processed_bytes
            eta = remaining_bytes / self.smoothed_speed

        return ProgressInfo(
            operation=self.operation,
            current_file=self.current_file,
            current_index=self.current_index,
            total_files=self.total_files,
            processed_bytes=self.processed_bytes,
            total_bytes=self.total_bytes,
            percent=percent,
            speed_bps=self.smoothed_speed,
            eta_seconds=eta,
        )

    def get_info(self) -> ProgressInfo:
        """Lấy thông tin tiến trình hiện tại."""
        percent = 1.0 if self.total_bytes == 0 else min(1.0, self.processed_bytes / max(self.total_bytes, 1))
        return ProgressInfo(
            operation=self.operation,
            current_file=self.current_file,
            current_index=self.current_index,
            total_files=self.total_files,
            processed_bytes=self.processed_bytes,
            total_bytes=self.total_bytes,
            percent=percent,
            speed_bps=self.smoothed_speed,
            eta_seconds=None,
        )
