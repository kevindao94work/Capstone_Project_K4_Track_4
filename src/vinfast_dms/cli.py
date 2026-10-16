"""Giao diện dòng lệnh cho demo webcam/video."""

from __future__ import annotations

import argparse
import sys
from contextlib import ExitStack
from dataclasses import replace
from pathlib import Path
from time import perf_counter

import cv2

from vinfast_dms.config import Config, load_config
from vinfast_dms.landmarks import LandmarkerError, MediaPipeLandmarker
from vinfast_dms.logging_utils import (
    CsvLogger,
    RecordingError,
    VideoRecorder,
    new_run_id,
    private_output_path,
    sha256_file,
)
from vinfast_dms.overlay import draw_overlay
from vinfast_dms.pipeline import DMSPipeline
from vinfast_dms.sources import SourceError, VideoSource
from vinfast_dms.temporal import STATE_LABELS_VI


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m vinfast_dms",
        description="Prototype quan sát mắt và tư thế đầu qua webcam hoặc video.",
        epilog="Không dùng prototype này khi lái xe thực tế.",
    )
    parser.add_argument("--source", default="camera", help="camera hoặc đường dẫn video.")
    parser.add_argument("--camera-index", type=int, default=0)
    parser.add_argument("--width", type=int, default=640)
    parser.add_argument("--height", type=int, default=480)
    parser.add_argument(
        "--max-frames", type=int, help="Giới hạn số khung hình; hữu ích ở chế độ headless."
    )
    parser.add_argument("--headless", action="store_true", help="Không mở cửa sổ OpenCV.")
    parser.add_argument("--config", type=Path, help="Đường dẫn cấu hình YAML.")
    parser.add_argument("--model", type=Path, help="Đường dẫn file face_landmarker.task.")
    parser.add_argument("--ear-closed", type=float)
    parser.add_argument("--ear-open", type=float)
    parser.add_argument("--closed-hold", type=float)
    parser.add_argument("--yaw-threshold", type=float)
    parser.add_argument("--distracted-hold", type=float)
    parser.add_argument("--max-gap", type=float)
    parser.add_argument(
        "--log-csv",
        nargs="?",
        const="auto",
        metavar="PATH",
        help="Bật log CSV; bỏ PATH để lưu tên tự sinh trong outputs/private/.",
    )
    parser.add_argument(
        "--record-output",
        nargs="?",
        const="auto",
        metavar="PATH",
        help="Ghi video có overlay theo lựa chọn chủ động; mặc định outputs/private/.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs/private"),
        help="Thư mục kết quả riêng tư mặc định.",
    )
    mirror = parser.add_mutually_exclusive_group()
    mirror.add_argument("--mirror", dest="mirror", action="store_true")
    mirror.add_argument("--no-mirror", dest="mirror", action="store_false")
    parser.set_defaults(mirror=None)
    return parser


def _configured(args: argparse.Namespace) -> Config:
    config = load_config(args.config)
    threshold_changes = {
        key: value
        for key, value in {
            "ear_closed": args.ear_closed,
            "ear_open": args.ear_open,
            "closed_hold_s": args.closed_hold,
            "yaw_distracted_deg": args.yaw_threshold,
            "distracted_hold_s": args.distracted_hold,
            "max_gap_s": args.max_gap,
        }.items()
        if value is not None
    }
    display_changes = {} if args.mirror is None else {"mirror": args.mirror}
    vision_changes = {} if args.model is None else {"model_path": str(args.model)}
    configured = replace(
        config,
        thresholds=replace(config.thresholds, **threshold_changes),
        display=replace(config.display, **display_changes),
        vision=replace(config.vision, **vision_changes),
    )
    configured.validate()
    return configured


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.max_frames is not None and args.max_frames < 1:
        parser.error("--max-frames phải lớn hơn 0.")
    if args.width < 1 or args.height < 1:
        parser.error("--width và --height phải lớn hơn 0.")
    if args.source == "camera" and args.headless and args.max_frames is None:
        parser.error("Webcam ở chế độ --headless cần --max-frames để kết thúc tự động.")
    try:
        config = _configured(args)
    except (OSError, ValueError) as exc:
        print(f"Cấu hình không hợp lệ: {exc}", file=sys.stderr)
        return 2

    model_path = Path(config.vision.model_path)
    count = 0
    warnings = 0
    recent_fps: list[float] = []
    last_loop = perf_counter()
    headless = args.headless
    run_id = new_run_id()
    log_path: Path | None = None
    if args.log_csv is not None:
        log_path = (
            private_output_path(args.output_dir, run_id, ".csv")
            if args.log_csv == "auto"
            else Path(args.log_csv)
        )
    recording_path: Path | None = None
    if args.record_output is not None:
        recording_path = (
            private_output_path(args.output_dir, run_id, ".mp4")
            if args.record_output == "auto"
            else Path(args.record_output)
        )
    try:
        with ExitStack() as stack:
            landmarker = stack.enter_context(
                MediaPipeLandmarker(model_path, max_faces=config.vision.num_faces)
            )
            import mediapipe as mp

            model_sha256 = sha256_file(model_path)
            source = stack.enter_context(
                VideoSource(
                    args.source,
                    camera_index=args.camera_index,
                    width=args.width,
                    height=args.height,
                    max_frames=args.max_frames,
                )
            )
            logger = None
            if log_path is not None:
                logger = stack.enter_context(
                    CsvLogger(
                        log_path,
                        run_id,
                        config.config_hash,
                        f"MediaPipe {mp.__version__}",
                        model_sha256,
                    )
                )
            pipeline = DMSPipeline(landmarker, config)
            recorder: VideoRecorder | None = None
            for sample in source:
                result = pipeline.process(sample)
                count += 1
                warnings += int(result.snapshot.warning)
                now = perf_counter()
                elapsed = now - last_loop
                if elapsed > 0.0:
                    recent_fps.append(1.0 / elapsed)
                    recent_fps = recent_fps[-30:]
                last_loop = now
                fps = sum(recent_fps) / len(recent_fps) if recent_fps else 0.0
                if logger is not None:
                    logger.write(sample, result)
                display = None
                if not headless or recording_path is not None:
                    display = draw_overlay(
                        sample.frame,
                        result,
                        fps,
                        mirror=config.display.mirror,
                    )
                if recording_path is not None:
                    if recorder is None:
                        recorder = stack.enter_context(
                            VideoRecorder(recording_path, source.fps or 30.0)
                        )
                    assert display is not None
                    recorder.write(display)
                if not headless:
                    assert display is not None
                    try:
                        cv2.imshow("VinFast DMS · Mẫu thử", display)
                        key = cv2.waitKey(1) & 0xFF
                    except cv2.error as exc:
                        headless = True
                        print(
                            f"Không mở được cửa sổ; tiếp tục headless: {exc}",
                            file=sys.stderr,
                        )
                        continue
                    if key == ord("q"):
                        break
                    if key == ord("r"):
                        pipeline.reset()
                    if key == ord("h"):
                        print("Phím: q thoát · r đặt lại · h trợ giúp")
    except (LandmarkerError, SourceError, OSError) as exc:
        print(f"Không thể chạy demo: {exc}", file=sys.stderr)
        return 2
    except RecordingError as exc:
        print(f"Không ghi được video đầu ra: {exc}", file=sys.stderr)
        return 3
    except KeyboardInterrupt:
        print("Đã dừng theo yêu cầu người dùng.")
    finally:
        try:
            cv2.destroyAllWindows()
        except cv2.error:
            pass
    print(f"Đã xử lý {count} khung hình; số khung đang cảnh báo: {warnings}.")
    if count == 0:
        print("Không có khung hình nào được xử lý.", file=sys.stderr)
        return 1
    print(f"Trạng thái cuối: {STATE_LABELS_VI[result.state]}.")
    if log_path is not None:
        print(f"Log CSV: {log_path}")
    if recording_path is not None:
        print(f"Video đầu ra: {recording_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
