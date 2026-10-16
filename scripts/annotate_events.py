#!/usr/bin/env python3
"""Gắn nhãn khoảng thời gian bằng thao tác thủ công của người đánh nhãn."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from vinfast_dms.metrics import (
    LABELS,
    EvaluationError,
    EventSegment,
    read_event_labels,
    write_event_labels,
)


def _interactive() -> tuple[float, float, str, str]:
    start = float(input("Thời điểm bắt đầu (giây): "))
    end = float(input("Thời điểm kết thúc (giây): "))
    label = input(f"Nhãn ({', '.join(LABELS)}): ").strip().upper()
    notes = input("Ghi chú (có thể để trống): ").strip()
    return start, end, label, notes


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("outputs/private/labels.csv"))
    parser.add_argument("--start-s", type=float)
    parser.add_argument("--end-s", type=float)
    parser.add_argument("--label", choices=LABELS)
    parser.add_argument("--annotator", default="Đào Gia Bảo")
    parser.add_argument("--notes", default="")
    args = parser.parse_args(argv)
    supplied = (args.start_s is not None, args.end_s is not None, args.label is not None)
    if any(supplied) and not all(supplied):
        parser.error("Cần truyền đủ --start-s, --end-s và --label hoặc nhập tương tác.")
    try:
        if all(supplied):
            start, end, label, notes = args.start_s, args.end_s, args.label, args.notes
        else:
            start, end, label, notes = _interactive()
        segment = EventSegment(start, end, label, args.annotator, notes)
        previous = read_event_labels(args.output) if args.output.is_file() else []
        combined = [*previous, segment]
        write_event_labels(args.output, combined)
    except (EvaluationError, OSError, ValueError, EOFError) as exc:
        print(f"Không lưu được nhãn: {exc}", file=sys.stderr)
        return 2
    print(f"Đã lưu nhãn thủ công vào {args.output}; tổng số đoạn: {len(combined)}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

