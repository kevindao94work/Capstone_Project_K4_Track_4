#!/usr/bin/env python3
"""Thử đọc số khung hình chỉ khi người dùng chủ động chạy script này."""

from __future__ import annotations

import argparse
import sys
from time import monotonic

from vinfast_dms.sources import SourceError, VideoSource


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--camera-index", type=int, default=0)
    parser.add_argument("--frames", type=int, default=30)
    parser.add_argument(
        "--duration-seconds",
        type=float,
        help="Giữ kiểm tra liên tục trong khoảng thời gian này.",
    )
    parser.add_argument("--width", type=int, default=640)
    parser.add_argument("--height", type=int, default=480)
    args = parser.parse_args()
    if args.frames < 1:
        parser.error("--frames phải lớn hơn 0.")
    if args.duration_seconds is not None and args.duration_seconds <= 0:
        parser.error("--duration-seconds phải lớn hơn 0.")
    try:
        with VideoSource(
            "camera", camera_index=args.camera_index, width=args.width, height=args.height
        ) as source:
            start = monotonic()
            count = 0
            while True:
                next(source)
                count += 1
                if args.duration_seconds is None and count >= args.frames:
                    break
                if (
                    args.duration_seconds is not None
                    and monotonic() - start >= args.duration_seconds
                ):
                    break
    except (SourceError, StopIteration) as exc:
        print(f"Camera check NOT RUN/BLOCKED: {exc}", file=sys.stderr)
        return 2
    if args.duration_seconds is None:
        print(f"camera smoke PASS: đã đọc {count} khung hình webcam thật.")
    else:
        print(
            f"camera smoke PASS: đã đọc {count} khung hình webcam thật trong "
            f"{args.duration_seconds:.1f} giây."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
