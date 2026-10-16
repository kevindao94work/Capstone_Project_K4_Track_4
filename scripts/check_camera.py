#!/usr/bin/env python3
"""Thử đọc số khung hình chỉ khi người dùng chủ động chạy script này."""

from __future__ import annotations

import argparse
import sys

from vinfast_dms.sources import SourceError, VideoSource


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--camera-index", type=int, default=0)
    parser.add_argument("--frames", type=int, default=30)
    parser.add_argument("--width", type=int, default=640)
    parser.add_argument("--height", type=int, default=480)
    args = parser.parse_args()
    if args.frames < 1:
        parser.error("--frames phải lớn hơn 0.")
    try:
        with VideoSource(
            "camera", camera_index=args.camera_index, width=args.width, height=args.height
        ) as source:
            samples = [next(source) for _ in range(args.frames)]
    except (SourceError, StopIteration) as exc:
        print(f"Camera check NOT RUN/BLOCKED: {exc}", file=sys.stderr)
        return 2
    print(f"camera smoke PASS: đã đọc {len(samples)} khung hình webcam thật.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
