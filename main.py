#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VietZIP 📦 — Ứng dụng nén và giải nén ZIP hiện đại, an toàn, giao diện tiếng Việt.
Khởi chạy chính thức:
    python main.py
"""

import os
import sys
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Thêm thư mục hiện tại vào sys.path để import chuẩn
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from vietzip.app import run_app

if __name__ == "__main__":
    run_app()
