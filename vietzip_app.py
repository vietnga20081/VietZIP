#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VietZIP 📦 — Ứng dụng nén và giải nén ZIP hiện đại, an toàn.
Tệp tương thích ngược chuyển tiếp trực tiếp vào kiến trúc module mới:
    python vietzip_app.py
hoặc
    python main.py
"""

import os
import sys

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from vietzip.app import run_app


def main():
    run_app()


if __name__ == "__main__":
    main()
