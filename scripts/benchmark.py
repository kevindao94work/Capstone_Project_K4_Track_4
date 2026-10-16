#!/usr/bin/env python3
"""Chạy benchmark offline từ manifest video và nhãn độc lập."""

from __future__ import annotations

import argparse
import csv
import json
import platform
import subprocess
import sys
from datetime import UTC, datetime
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

from vinfast_dms.config import load_config
from vinfast_dms.logging_utils import sha256_file
from vinfast_dms.metrics import (
    EvaluationError,
    evaluate_predictions,
    instant_baseline,
    read_event_labels,
    read_predictions,
)


def read_manifest(path: str | Path) -> list[dict[str, Path]]:
    manifest_path = Path(path).expanduser().resolve()
    if not manifest_path.is_file():
        raise EvaluationError(f"Không tìm thấy manifest: {manifest_path}")
    with manifest_path.open(newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        required = {"source", "labels"}
        if required - set(reader.fieldnames or ()):
            raise EvaluationError("Manifest CSV cần hai cột source, labels.")
        entries: list[dict[str, Path]] = []
        for row_number, row in enumerate(reader, start=2):
            source = (row.get("source") or "").strip()
            labels = (row.get("labels") or "").strip()
            if not source or not labels:
                raise EvaluationError(f"Thiếu source hoặc labels ở dòng {row_number}.")
            source_path = (manifest_path.parent / source).resolve()
            labels_path = (manifest_path.parent / labels).resolve()
            if not source_path.is_file():
                raise EvaluationError(f"Không tìm thấy video ở dòng {row_number}: {source_path}")
            if not labels_path.is_file():
                raise EvaluationError(f"Không tìm thấy CSV nhãn ở dòng {row_number}: {labels_path}")
            entries.append({"source": source_path, "labels": labels_path})
    if not entries:
        raise EvaluationError("Manifest không có video; NOT EVALUATED.")
    return entries


def _package_version(package: str) -> str | None:
    try:
        return version(package)
    except PackageNotFoundError:
        return None


def _environment(model_path: Path) -> dict[str, object]:
    return {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "architecture": platform.machine(),
        "processor": platform.processor() or None,
        "packages": {
            "vinfast-dms": _package_version("vinfast-dms"),
            "mediapipe": _package_version("mediapipe"),
            "opencv-contrib-python": _package_version("opencv-contrib-python"),
            "numpy": _package_version("numpy"),
        },
        "model_sha256": sha256_file(model_path),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/private/benchmark"))
    parser.add_argument("--model", type=Path)
    parser.add_argument("--config", type=Path)
    parser.add_argument("--max-frames", type=int)
    args = parser.parse_args(argv)
    if args.max_frames is not None and args.max_frames < 1:
        parser.error("--max-frames phải lớn hơn 0.")

    try:
        entries = read_manifest(args.manifest)
        config = load_config(args.config)
        model_path = args.model or Path(config.vision.model_path)
        if not model_path.is_file():
            raise EvaluationError(f"Không tìm thấy model Face Landmarker: {model_path}")
        output_root = args.output_dir.expanduser()
        run_stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        run_dir = output_root / f"benchmark_{run_stamp}"
        run_dir.mkdir(parents=True, exist_ok=False)

        results: list[dict[str, object]] = []
        for index, entry in enumerate(entries, start=1):
            label_segments = read_event_labels(entry["labels"])
            if not label_segments:
                raise EvaluationError(f"Video {index} không có đoạn ground truth; NOT EVALUATED.")
            prediction_path = run_dir / f"sample_{index:03d}_predictions.csv"
            command = [
                sys.executable,
                "-m",
                "vinfast_dms",
                "--source",
                str(entry["source"]),
                "--headless",
                "--model",
                str(model_path),
                "--log-csv",
                str(prediction_path),
            ]
            if args.config is not None:
                command.extend(["--config", str(args.config)])
            if args.max_frames is not None:
                command.extend(["--max-frames", str(args.max_frames)])
            completed = subprocess.run(command, capture_output=True, text=True, check=False)
            if completed.returncode != 0:
                message = completed.stderr.strip() or completed.stdout.strip()
                raise EvaluationError(f"Benchmark video {index} thất bại: {message}")
            predictions = read_predictions(prediction_path)
            temporal = evaluate_predictions(predictions, label_segments)
            baseline_predictions = instant_baseline(predictions, config.thresholds)
            baseline = evaluate_predictions(baseline_predictions, label_segments)
            results.append(
                {
                    "sample": index,
                    "source": entry["source"].name,
                    "labels": entry["labels"].name,
                    "prediction_log": prediction_path.name,
                    "temporal": temporal,
                    "instant_baseline": baseline,
                }
            )
    except (EvaluationError, OSError, ValueError) as exc:
        print(f"NOT EVALUATED: {exc}", file=sys.stderr)
        return 2

    report = {
        "evaluation_status": "EVALUATED",
        "generated_at_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "manifest": Path(args.manifest).name,
        "model": str(model_path),
        "config_hash": config.config_hash,
        "max_frames_per_video": args.max_frames,
        "environment": _environment(model_path),
        "results": results,
        "interpretation": (
            "Các số đo chỉ áp dụng cho những video đã gắn nhãn trong manifest; "
            "không suy rộng sang người lái hoặc điều kiện khác."
        ),
    }
    report_path = run_dir / "benchmark_report.json"
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(f"Đã lưu báo cáo và log riêng tư: {run_dir}")
    for item in results:
        temporal = item["temporal"]
        assert isinstance(temporal, dict)
        print(
            f"Video {item['sample']}: {temporal['labeled_frames']} frame có nhãn; "
            f"coverage={temporal['coverage']}; "
            f"F1 mắt={temporal['per_class']['EYES_CLOSED']['f1']}; "
            f"F1 mất tập trung={temporal['per_class']['DISTRACTED']['f1']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
