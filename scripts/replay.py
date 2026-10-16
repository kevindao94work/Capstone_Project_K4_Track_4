#!/usr/bin/env python3
"""Chạy lại video offline và so sánh chuỗi dự đoán giữa nhiều lượt."""

from __future__ import annotations

import argparse
import csv
import subprocess
import sys
import tempfile
from pathlib import Path

from vinfast_dms.logging_utils import deterministic_row


def _read_log(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source", required=True, help="Đường dẫn video; replay không hỗ trợ webcam."
    )
    parser.add_argument("--runs", type=int, default=2)
    parser.add_argument("--max-frames", type=int)
    parser.add_argument("--model", type=Path)
    parser.add_argument("--config", type=Path)
    args = parser.parse_args(argv)
    if args.source == "camera":
        parser.error("Replay chỉ nhận video đã lưu; không hỗ trợ camera trực tiếp.")
    if args.runs < 2:
        parser.error("--runs phải lớn hơn hoặc bằng 2.")
    if args.max_frames is not None and args.max_frames < 1:
        parser.error("--max-frames phải lớn hơn 0.")
    reference: list[tuple[tuple[str, str], ...]] | None = None
    with tempfile.TemporaryDirectory(prefix="vinfast-dms-replay-") as temp:
        for run_index in range(args.runs):
            csv_path = Path(temp) / f"run_{run_index}.csv"
            command = [
                sys.executable,
                "-m",
                "vinfast_dms",
                "--source",
                args.source,
                "--headless",
                "--log-csv",
                str(csv_path),
            ]
            if args.max_frames is not None:
                command.extend(["--max-frames", str(args.max_frames)])
            if args.model is not None:
                command.extend(["--model", str(args.model)])
            if args.config is not None:
                command.extend(["--config", str(args.config)])
            completed = subprocess.run(command, capture_output=True, text=True, check=False)
            if completed.returncode != 0:
                print(completed.stderr or completed.stdout, file=sys.stderr)
                return completed.returncode
            rows = _read_log(csv_path)
            signature = [deterministic_row(row) for row in rows]
            if reference is None:
                reference = signature
            elif signature != reference:
                print(f"Replay không tái lập ở lượt {run_index + 1}.", file=sys.stderr)
                return 1
    print(f"Replay tái lập: {args.runs} lượt, {len(reference or [])} khung hình.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
