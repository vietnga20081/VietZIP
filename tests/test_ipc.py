"""Tests for IPC Single-Instance service and path normalization."""

import os
import time
from pathlib import Path
from vietzip.services.ipc_service import (
    SingleInstanceServer,
    normalize_input_path,
    send_to_primary_instance,
)


def test_normalize_input_path():
    assert normalize_input_path("") == ""
    assert normalize_input_path('  "C:\\test\\file.txt"  ') == os.path.normpath("C:\\test\\file.txt")
    # Windows escaped quote
    assert normalize_input_path('C:\\test\\folder\\"') == os.path.normpath("C:\\test\\folder")
    assert normalize_input_path('C:\\test\\folder\\') == os.path.normpath("C:\\test\\folder")
    # Drive root preserved
    assert normalize_input_path('C:\\') == os.path.normpath("C:\\")


def test_ipc_communication(tmp_path):
    received = []

    def on_recv(action, paths):
        received.append((action, paths))

    test_file = tmp_path / "sample.txt"
    test_file.write_text("hello", encoding="utf-8")

    server = SingleInstanceServer(on_recv)
    started = server.start()
    assert started, "Server should start on port"

    try:
        ok = send_to_primary_instance("compress", [str(test_file)], timeout=1.0)
        assert ok, "send_to_primary_instance should succeed"

        # Give background thread time to process
        for _ in range(20):
            if received:
                break
            time.sleep(0.05)

        assert len(received) == 1
        assert received[0][0] == "compress"
        assert str(test_file) in received[0][1]
    finally:
        server.stop()
