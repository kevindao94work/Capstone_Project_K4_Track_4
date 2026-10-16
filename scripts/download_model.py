#!/usr/bin/env python3
"""Tải model Face Landmarker từ bộ lưu trữ Google chính thức."""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path
from urllib.request import urlopen

MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/face_landmarker/"
    "face_landmarker/float16/latest/face_landmarker.task"
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as model:
        for block in iter(lambda: model.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("models/face_landmarker.task"))
    parser.add_argument("--force", action="store_true", help="Tải đè model đang có.")
    parser.add_argument("--sha256", help="Từ chối model nếu SHA-256 không khớp.")
    args = parser.parse_args(argv)
    if args.output.exists() and not args.force:
        digest = sha256_file(args.output)
        if args.sha256 and digest.lower() != args.sha256.lower():
            print("SHA-256 model hiện có không khớp.", file=sys.stderr)
            return 2
        print(f"Model đã có: {args.output} (SHA-256 {digest})")
        return 0
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_suffix(args.output.suffix + ".download")
    try:
        with urlopen(MODEL_URL, timeout=60) as response, temporary.open("wb") as target:
            if response.status != 200:
                raise OSError(f"Máy chủ trả mã HTTP {response.status}.")
            while block := response.read(1024 * 1024):
                target.write(block)
        if temporary.stat().st_size < 1_000_000:
            raise OSError("Tệp tải về nhỏ bất thường, không phải gói model hợp lệ.")
        digest = sha256_file(temporary)
        if args.sha256 and digest.lower() != args.sha256.lower():
            raise OSError("SHA-256 tải về không khớp giá trị được cung cấp.")
        temporary.replace(args.output)
    except Exception as exc:
        temporary.unlink(missing_ok=True)
        print(f"Không tải được model: {exc}", file=sys.stderr)
        return 1
    print(f"Đã tải model chính thức: {args.output}")
    print(f"SHA-256: {digest}")
    print("Nguồn: Google MediaPipe Models; model không được commit vào repository.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
