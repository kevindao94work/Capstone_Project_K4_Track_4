#!/usr/bin/env python3
"""Đánh giá dự đoán CSV bằng các đoạn ground truth được gắn nhãn độc lập."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from vinfast_dms.config import load_config
from vinfast_dms.metrics import (
    EvaluationError,
    evaluate_predictions,
    instant_baseline,
    read_event_labels,
    read_predictions,
)


def _format(value: object) -> str:
    if value is None:
        return "N/A"
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--labels", type=Path, required=True)
    parser.add_argument("--config", type=Path)
    parser.add_argument("--output", type=Path, help="Tùy chọn: lưu báo cáo JSON.")
    args = parser.parse_args(argv)
    try:
        predictions = read_predictions(args.predictions)
        labels = read_event_labels(args.labels)
        temporal = evaluate_predictions(predictions, labels)
        config = load_config(args.config)
        baseline_rows = instant_baseline(predictions, config.thresholds)
        baseline = evaluate_predictions(baseline_rows, labels)
    except (EvaluationError, OSError, ValueError) as exc:
        print(f"NOT EVALUATED: {exc}", file=sys.stderr)
        return 2
    report = {
        "evaluation_status": "EVALUATED",
        "prediction_file": str(args.predictions),
        "label_file": str(args.labels),
        "labeling_note": "Nhãn phải được người đánh giá kiểm tra độc lập; không sinh từ dự đoán.",
        "temporal": temporal,
        "instant_baseline": baseline,
    }
    content = json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False)
    if args.output is None:
        print(content)
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(content + "\n", encoding="utf-8")
        print(f"Đã lưu báo cáo đánh giá: {args.output}")
    print(
        "Độ phủ temporal: "
        f"{_format(temporal['coverage'])}; F1 nhắm mắt: "
        f"{_format(temporal['per_class']['EYES_CLOSED']['f1'])}; "
        f"F1 mất tập trung: {_format(temporal['per_class']['DISTRACTED']['f1'])}."
    )
    print(
        "Độ trễ xử lý p50/p95: "
        f"{_format(temporal['processing_latency_ms_p50'])}/"
        f"{_format(temporal['processing_latency_ms_p95'])} ms; "
        "độ trễ sự kiện được tính theo source_time_s."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

