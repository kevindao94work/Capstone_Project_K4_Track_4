#!/usr/bin/env python3
"""Kiểm tra các thư viện và API cần thiết trên máy hiện tại."""

from __future__ import annotations

import platform
import sys


def main() -> int:
    print(f"Python: {sys.version.split()[0]} ({platform.machine()})")
    if sys.version_info < (3, 11) or sys.version_info >= (3, 13):
        print("KHÔNG ĐẠT: cần Python 3.11 hoặc 3.12.")
        return 1
    if platform.machine() not in {"arm64", "aarch64", "x86_64", "AMD64"}:
        print("CẢNH BÁO: kiến trúc chưa được kiểm chứng.")
    try:
        import cv2
        import mediapipe as mp
        import numpy as np

        from vinfast_dms.config import load_config
    except ImportError as exc:
        print(f"THIẾU THƯ VIỆN: {exc}")
        return 1
    config = load_config()
    tasks_api = hasattr(mp, "tasks") and hasattr(mp.tasks, "vision")
    print(f"NumPy: {np.__version__}; OpenCV: {cv2.__version__}")
    print(f"MediaPipe: {mp.__version__}; FaceLandmarker Tasks: {'có' if tasks_api else 'không'}")
    print(f"OpenCV solvePnP: {'có' if hasattr(cv2, 'solvePnP') else 'không'}")
    print(f"Cấu hình hợp lệ: {config.config_hash[:12]}")
    return 0 if tasks_api and hasattr(cv2, "solvePnP") else 1


if __name__ == "__main__":
    raise SystemExit(main())
