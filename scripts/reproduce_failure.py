#!/usr/bin/env python3
"""Chạy lại video và trích cửa sổ thời gian để phân tích một lỗi quan sát được."""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

from vinfast_dms.metrics import EvaluationError, EventSegment, read_event_labels

PREDICTION_FIELDS = (
    "source_time_s",
    "state",
    "quality_valid",
    "quality_reason",
    "ear_mean",
    "yaw_deg",
    "warning",
)


def _label_at(segments: list[EventSegment], timestamp_s: float) -> str | None:
    return next(
        (
            segment.label
            for segment in segments
            if segment.start_s <= timestamp_s < segment.end_s
        ),
        None,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source", type=Path, required=True, help="Video có consent, giữ riêng tư."
    )
    parser.add_argument("--time-s", type=float, required=True, help="Mốc thời gian trong clip.")
    parser.add_argument("--window-s", type=float, default=2.0)
    parser.add_argument("--labels", type=Path, help="CSV nhãn kiểm tra độc lập (tùy chọn).")
    parser.add_argument("--model", type=Path)
    parser.add_argument("--config", type=Path)
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/private/failures"))
    args = parser.parse_args(argv)
    if not args.source.is_file():
        parser.error(f"Không tìm thấy video: {args.source}")
    if args.source.suffix.lower() not in {".avi", ".mp4", ".m4v", ".mov", ".webm"}:
        parser.error("Nguồn cần là tệp video được hỗ trợ.")
    if args.time_s < 0.0 or args.window_s <= 0.0:
        parser.error("--time-s phải không âm và --window-s phải lớn hơn 0.")

    try:
        labels = read_event_labels(args.labels) if args.labels is not None else []
        stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        output_dir = args.output_dir.expanduser()
        output_dir.mkdir(parents=True, exist_ok=True)
        prediction_path = output_dir / f"failure_replay_{stamp}.csv"
        report_path = output_dir / f"failure_window_{stamp}.json"
        command = [
            sys.executable,
            "-m",
            "vinfast_dms",
            "--source",
            str(args.source),
            "--headless",
            "--log-csv",
            str(prediction_path),
        ]
        if args.model is not None:
            command.extend(["--model", str(args.model)])
        if args.config is not None:
            command.extend(["--config", str(args.config)])
        completed = subprocess.run(command, capture_output=True, text=True, check=False)
        if completed.returncode != 0:
            message = completed.stderr.strip() or completed.stdout.strip()
            raise EvaluationError(f"Chạy lại video thất bại: {message}")
        start_s = max(0.0, args.time_s - args.window_s / 2.0)
        end_s = args.time_s + args.window_s / 2.0
        with prediction_path.open(newline="", encoding="utf-8-sig") as file:
            reader = csv.DictReader(file)
            if not set(PREDICTION_FIELDS).issubset(reader.fieldnames or ()):
                raise EvaluationError("Log thiếu trường cần để phân tích cửa sổ lỗi.")
            rows = [
                row
                for row in reader
                if start_s <= float(row["source_time_s"]) <= end_s
            ]
        if not rows:
            raise EvaluationError("Không có frame trong cửa sổ thời gian đã chọn.")
        for row in rows:
            row["expected_label"] = _label_at(labels, float(row["source_time_s"])) or ""
        report = {
            "source_name": args.source.name,
            "requested_time_s": args.time_s,
            "window_start_s": start_s,
            "window_end_s": end_s,
            "independent_labels_supplied": bool(labels),
            "rows": rows,
            "interpretation": (
                "Chưa có nhãn độc lập; đây chỉ là cửa sổ dự đoán, không chứng minh lỗi."
                if not labels
                else (
                    "Đối chiếu nhãn cần người đánh giá xác nhận; sai khác không tự xác định "
                    "root cause."
                )
            ),
        }
        report_path.write_text(
            json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
            encoding="utf-8",
        )
    except (EvaluationError, OSError, ValueError) as exc:
        print(f"NOT DEMONSTRATED: {exc}", file=sys.stderr)
        return 2

    print(f"Đã lưu CSV replay: {prediction_path}")
    print(f"Đã lưu cửa sổ phân tích riêng tư: {report_path}")
    print(report["interpretation"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
