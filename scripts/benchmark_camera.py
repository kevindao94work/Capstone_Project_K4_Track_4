#!/usr/bin/env python3
"""Đo pipeline trên webcam trực tiếp, chỉ giữ số liệu tổng hợp trong RAM."""

from __future__ import annotations

import argparse
import json
import platform
import sys
from collections import Counter
from contextlib import ExitStack
from datetime import UTC, datetime
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from time import perf_counter

import cv2
import numpy as np

from vinfast_dms.config import load_config
from vinfast_dms.landmarks import LandmarkerError, MediaPipeLandmarker
from vinfast_dms.logging_utils import sha256_file
from vinfast_dms.overlay import draw_overlay
from vinfast_dms.pipeline import DMSPipeline
from vinfast_dms.sources import DEFAULT_CAMERA_INDEX, SourceError, VideoSource

GUIDED_PHASES = (
    (0.0, 8.0, "normal", "LOOK STRAIGHT / EYES OPEN", "NORMAL"),
    (8.0, 14.0, "blink", "BLINK NATURALLY", "NORMAL"),
    (14.0, 22.0, "eyes_closed", "CLOSE EYES 2S, THEN OPEN", "EYES_CLOSED"),
    (22.0, 29.0, "turn_left", "TURN HEAD LEFT, THEN RETURN", "DISTRACTED"),
    (29.0, 36.0, "turn_right", "TURN HEAD RIGHT, THEN RETURN", "DISTRACTED"),
    (36.0, 42.0, "out_of_view", "MOVE OUT OF VIEW, THEN RETURN", "UNKNOWN"),
    (42.0, 49.0, "cover_eyes", "COVER EYES BRIEFLY, THEN UNCOVER", "UNKNOWN"),
    (49.0, 56.0, "poor_light", "OPTIONAL: DIM ROOM LIGHT BRIEFLY", "UNKNOWN"),
    (56.0, 60.0, "recovery", "LOOK STRAIGHT / EYES OPEN", "NORMAL"),
)
INTERACTIVE_SCENARIOS = (
    ("normal", "Nhìn thẳng, mở mắt", 6.0, "NORMAL", False),
    ("blink", "Chớp mắt tự nhiên một lần", 6.0, "NORMAL", False),
    ("eyes_closed", "Nhắm mắt 2 giây rồi mở mắt", 7.0, "EYES_CLOSED", False),
    ("turn_left", "Quay trái, giữ 2 giây rồi quay về", 7.0, "DISTRACTED", False),
    ("turn_right", "Quay phải, giữ 2 giây rồi quay về", 7.0, "DISTRACTED", False),
    ("out_of_view", "Ra khỏi khung 2 giây rồi quay lại", 6.0, "UNKNOWN", False),
    ("cover_eyes", "Che mắt 2 giây rồi bỏ che", 6.0, "UNKNOWN", False),
    ("poor_light", "TÙY CHỌN: giảm sáng nhẹ trong chốc lát", 6.0, "UNKNOWN", True),
    ("recovery", "Nhìn thẳng, mở mắt", 5.0, "NORMAL", False),
)
SCENARIO_STAGES: dict[str, tuple[tuple[float, float, str, str, str], ...]] = {
    "normal": ((0.0, 6.0, "steady_state", "Nhìn thẳng, mở mắt", "NORMAL"),),
    "blink": (
        (0.0, 2.0, "baseline", "Nhìn thẳng, mở mắt", "NORMAL"),
        (2.0, 2.5, "transition", "Chớp mắt một lần", "NORMAL"),
        (2.5, 6.0, "recovery", "Nhìn thẳng, mở mắt", "NORMAL"),
    ),
    "eyes_closed": (
        (0.0, 1.0, "transition", "Nhắm mắt", "NORMAL"),
        (1.0, 3.0, "hold", "Giữ mắt nhắm", "EYES_CLOSED"),
        (3.0, 7.0, "recovery", "Mở mắt, nhìn thẳng", "NORMAL"),
    ),
    "turn_left": (
        (0.0, 1.0, "transition", "Quay đầu sang trái", "NORMAL"),
        (1.0, 3.0, "hold", "Giữ đầu quay trái", "DISTRACTED"),
        (3.0, 7.0, "recovery", "Quay lại nhìn thẳng", "NORMAL"),
    ),
    "turn_right": (
        (0.0, 1.0, "transition", "Quay đầu sang phải", "NORMAL"),
        (1.0, 3.0, "hold", "Giữ đầu quay phải", "DISTRACTED"),
        (3.0, 7.0, "recovery", "Quay lại nhìn thẳng", "NORMAL"),
    ),
    "out_of_view": (
        (0.0, 1.0, "transition", "Di chuyển ra khỏi khung hình", "UNKNOWN"),
        (1.0, 3.0, "hold", "Ở ngoài khung hình", "UNKNOWN"),
        (3.0, 6.0, "recovery", "Quay lại nhìn thẳng", "NORMAL"),
    ),
    "cover_eyes": (
        (0.0, 1.0, "transition", "Che mắt", "UNKNOWN"),
        (1.0, 3.0, "hold", "Giữ che mắt", "UNKNOWN"),
        (3.0, 6.0, "recovery", "Bỏ che, nhìn thẳng", "NORMAL"),
    ),
    "poor_light": (
        (0.0, 1.0, "transition", "Giảm sáng nhẹ", "UNKNOWN"),
        (1.0, 4.0, "hold", "Giữ ánh sáng yếu", "UNKNOWN"),
        (4.0, 6.0, "recovery", "Khôi phục ánh sáng", "NORMAL"),
    ),
    "recovery": ((0.0, 5.0, "steady_state", "Nhìn thẳng, mở mắt", "NORMAL"),),
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--camera-index", type=int, default=DEFAULT_CAMERA_INDEX)
    parser.add_argument("--duration-seconds", type=float, default=30.0)
    parser.add_argument("--width", type=int, default=640)
    parser.add_argument("--height", type=int, default=480)
    parser.add_argument("--model", type=Path)
    parser.add_argument("--config", type=Path)
    parser.add_argument(
        "--guided-scenarios",
        action="store_true",
        help="Chạy 60 giây cue trực tiếp trên cửa sổ, chỉ lưu thống kê theo pha.",
    )
    parser.add_argument(
        "--interactive-scenarios",
        action="store_true",
        help="Hiện từng tình huống; nhấn Space khi sẵn sàng, s để bỏ qua ánh sáng, q để dừng.",
    )
    parser.add_argument(
        "--scenario",
        action="append",
        choices=[scenario[0] for scenario in INTERACTIVE_SCENARIOS],
        help=(
            "Chỉ chạy tình huống tương tác đã chọn; có thể lặp cờ để chọn nhiều "
            "pha. Mặc định chạy tất cả."
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Tùy chọn lưu JSON thống kê; không lưu frame, đặc trưng hoặc video.",
    )
    return parser


def _package_version(name: str) -> str | None:
    try:
        return version(name)
    except PackageNotFoundError:
        return None


def _percentile(values: list[float], percentile: float) -> float | None:
    if not values:
        return None
    return float(np.percentile(values, percentile))


def _new_measurement_stats() -> dict[str, object]:
    return {
        "frames": 0,
        "face_detected_frames": 0,
        "landmark_quality_gate_passed_frames": 0,
        "pipeline_valid_frames": 0,
        "warning_frames": 0,
        "observed_states": Counter(),
        "quality_reasons": Counter(),
        "processing_ms": [],
        "reprojection_error_px": [],
        "valid_yaw_deg": [],
        "valid_pitch_deg": [],
        "valid_roll_deg": [],
        "first_frame_index": None,
        "last_frame_index": None,
        "source_start_s": None,
        "source_end_s": None,
    }


def _new_scenario_stats() -> dict[str, object]:
    stats = _new_measurement_stats()
    stats["subphases"] = {}
    return stats


def _record_measurement(
    stats: dict[str, object],
    sample,
    result,
    stage_name: str | None = None,
    phase_elapsed_s: float | None = None,
) -> None:
    stats["frames"] = int(stats["frames"]) + 1
    stats["face_detected_frames"] = int(stats["face_detected_frames"]) + int(
        result.face_detected
    )
    stats["landmark_quality_gate_passed_frames"] = int(
        stats["landmark_quality_gate_passed_frames"]
    ) + int(result.face_landmarks is not None)
    stats["pipeline_valid_frames"] = int(stats["pipeline_valid_frames"]) + int(
        result.quality_valid
    )
    stats["warning_frames"] = int(stats["warning_frames"]) + int(
        result.snapshot.warning
    )
    states = stats["observed_states"]
    reasons = stats["quality_reasons"]
    latencies = stats["processing_ms"]
    errors = stats["reprojection_error_px"]
    yaws = stats["valid_yaw_deg"]
    pitches = stats["valid_pitch_deg"]
    rolls = stats["valid_roll_deg"]
    assert isinstance(states, Counter)
    assert isinstance(reasons, Counter)
    assert isinstance(latencies, list)
    assert isinstance(errors, list)
    assert isinstance(yaws, list)
    assert isinstance(pitches, list)
    assert isinstance(rolls, list)
    states[result.state.value] += 1
    reasons[result.quality_reason or "valid"] += 1
    latencies.append(result.processing_ms)
    if result.head_pose is not None:
        error = result.head_pose.reprojection_error_px
        if error is not None:
            errors.append(error)
        if result.head_pose.valid:
            assert result.head_pose.yaw_deg is not None
            assert result.head_pose.pitch_deg is not None
            assert result.head_pose.roll_deg is not None
            yaws.append(result.head_pose.yaw_deg)
            pitches.append(result.head_pose.pitch_deg)
            rolls.append(result.head_pose.roll_deg)
    if stats["first_frame_index"] is None:
        stats["first_frame_index"] = sample.index
        stats["source_start_s"] = sample.timestamp_s
    stats["last_frame_index"] = sample.index
    stats["source_end_s"] = sample.timestamp_s

    if stage_name is not None:
        subphases = stats["subphases"]
        assert isinstance(subphases, dict)
        subphase = subphases.setdefault(stage_name, _new_measurement_stats())
        assert isinstance(subphase, dict)
        _record_measurement(subphase, sample, result)
        offsets = subphase.setdefault("observed_phase_offsets_s", [])
        assert isinstance(offsets, list)
        if phase_elapsed_s is not None:
            offsets.append(phase_elapsed_s)


def _measurement_summary(stats: dict[str, object]) -> dict[str, object]:
    frames = int(stats["frames"])
    observed_states = stats["observed_states"]
    quality_reasons = stats["quality_reasons"]
    processing_ms = stats["processing_ms"]
    errors = stats["reprojection_error_px"]
    yaws = stats["valid_yaw_deg"]
    pitches = stats["valid_pitch_deg"]
    rolls = stats["valid_roll_deg"]
    assert isinstance(observed_states, Counter)
    assert isinstance(quality_reasons, Counter)
    assert isinstance(processing_ms, list)
    assert isinstance(errors, list)
    assert isinstance(yaws, list)
    assert isinstance(pitches, list)
    assert isinstance(rolls, list)
    offsets = stats.get("observed_phase_offsets_s", [])
    assert isinstance(offsets, list)
    return {
        "frames": frames,
        "face_detected_frames": int(stats["face_detected_frames"]),
        "face_detection_rate": (
            int(stats["face_detected_frames"]) / frames if frames else None
        ),
        "landmark_quality_gate_passed_frames": int(
            stats["landmark_quality_gate_passed_frames"]
        ),
        "pipeline_valid_frames": int(stats["pipeline_valid_frames"]),
        "pipeline_valid_rate": (
            int(stats["pipeline_valid_frames"]) / frames if frames else None
        ),
        "warning_frames": int(stats["warning_frames"]),
        "observed_states": dict(sorted(observed_states.items())),
        "quality_reasons": dict(sorted(quality_reasons.items())),
        "processing_latency_ms_p50": _percentile(processing_ms, 50),
        "processing_latency_ms_p95": _percentile(processing_ms, 95),
        "reprojection_error_px": {
            "valid_measurements": len(errors),
            "median": _percentile(errors, 50),
            "p95": _percentile(errors, 95),
            "maximum": max(errors) if errors else None,
            "note": "Bao gồm residual trước quality gate; bỏ qua frame không tạo được pose.",
        },
        "valid_pose_orientation_deg": {
            "measurements": len(yaws),
            "yaw_median": _percentile(yaws, 50),
            "yaw_p05": _percentile(yaws, 5),
            "yaw_p95": _percentile(yaws, 95),
            "pitch_median": _percentile(pitches, 50),
            "roll_median": _percentile(rolls, 50),
        },
        "frame_boundaries": {
            "first_frame_index": stats["first_frame_index"],
            "last_frame_index": stats["last_frame_index"],
            "source_start_s": stats["source_start_s"],
            "source_end_s": stats["source_end_s"],
        },
        "observed_phase_offset_seconds": (
            [min(offsets), max(offsets)] if offsets else None
        ),
    }


def _scenario_summary(
    scenario: tuple[str, str, float, str, bool],
    stats: dict[str, object],
    status: str,
    duration_s: float,
) -> dict[str, object]:
    subphases = stats["subphases"]
    assert isinstance(subphases, dict)
    stage_summaries: dict[str, object] = {}
    for stage in SCENARIO_STAGES[scenario[0]]:
        start_s, end_s, name, instruction, expected = stage
        stage_stats = subphases.get(name, _new_measurement_stats())
        assert isinstance(stage_stats, dict)
        stage_summaries[name] = {
            "requested_action": instruction,
            "expected_state_hypothesis": expected,
            "planned_offset_seconds": [start_s, end_s],
            **_measurement_summary(stage_stats),
        }
    return {
        "scenario": scenario[0],
        "requested_action": scenario[1],
        "expected_state_hypothesis": scenario[3],
        "status": status,
        "measured_duration_seconds": duration_s,
        **_measurement_summary(stats),
        "subphases": stage_summaries,
        "evaluation_note": (
            "Ranh giới subphase theo cue/time tính từ Space; đây là giả thuyết "
            "thao tác, không phải nhãn độc lập."
        ),
    }


def run_interactive_scenario_check(args: argparse.Namespace) -> dict[str, object]:
    config = load_config(args.config)
    model_path = args.model or Path(config.vision.model_path)
    if not model_path.is_file():
        raise LandmarkerError(
            f"Thiếu model Face Landmarker: {model_path}. "
            "Tải bằng `python scripts/download_model.py`."
        )
    source = VideoSource(
        "camera",
        camera_index=args.camera_index,
        width=args.width,
        height=args.height,
    )
    scenario_results: list[dict[str, object]] = []
    selected_names = getattr(args, "scenario", None)
    scenarios = tuple(
        scenario
        for scenario in INTERACTIVE_SCENARIOS
        if selected_names is None or scenario[0] in selected_names
    )
    capture_error: str | None = None
    display_status = "DISPLAYED"
    backend_name: str | None = None
    capture_width: float | None = None
    capture_height: float | None = None
    scenario_index = 0
    active_started: float | None = None
    active_stats: dict[str, object] | None = None
    session_start = perf_counter()
    try:
        with ExitStack() as stack:
            landmarker = stack.enter_context(
                MediaPipeLandmarker(model_path, max_faces=config.vision.num_faces)
            )
            stack.enter_context(source)
            assert source.capture is not None
            try:
                backend_name = source.capture.getBackendName()
                width_value = float(source.capture.get(cv2.CAP_PROP_FRAME_WIDTH))
                height_value = float(source.capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
                capture_width = width_value if width_value > 0 else None
                capture_height = height_value if height_value > 0 else None
            except cv2.error:
                pass
            pipeline = DMSPipeline(landmarker, config)
            while (
                scenario_index < len(scenarios)
                and perf_counter() - session_start < 600.0
            ):
                sample = next(source)
                frame_read_at = perf_counter()
                result = pipeline.process(sample)
                scenario = scenarios[scenario_index]
                phase_elapsed = (
                    frame_read_at - active_started if active_started is not None else 0.0
                )
                if active_started is not None:
                    assert active_stats is not None
                    stage = next(
                        (
                            item
                            for item in SCENARIO_STAGES[scenario[0]]
                            if item[0] <= phase_elapsed < item[1]
                        ),
                        None,
                    )
                    if stage is not None:
                        _start_s, end_s, stage_name, instruction, _expected = stage
                        _record_measurement(
                            active_stats,
                            sample,
                            result,
                            stage_name,
                            phase_elapsed,
                        )
                        prompt = (
                            f"PHA {stage_name}: {instruction} · "
                            f"{max(0.0, end_s - phase_elapsed):.1f}s"
                        )
                    else:
                        prompt = (
                            "Kết thúc pha · "
                            f"{max(0.0, scenario[2] - phase_elapsed):.1f}s"
                        )
                else:
                    optional_hint = " · nhấn S để bỏ qua" if scenario[4] else ""
                    prompt = f"SẴN SÀNG: {scenario[1]} · NHẤN SPACE{optional_hint}"

                try:
                    display = draw_overlay(
                        sample.frame,
                        result,
                        0.0,
                        mirror=config.display.mirror,
                    )
                    cv2.putText(
                        display,
                        prompt,
                        (10, 25),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.48,
                        (255, 255, 255),
                        2,
                        cv2.LINE_AA,
                    )
                    cv2.imshow("VinFast DMS · Kiểm tra tình huống", display)
                    key = cv2.waitKey(1) & 0xFF
                except cv2.error as exc:
                    display_status = "UNAVAILABLE"
                    print(
                        f"Không mở được cửa sổ kiểm thử tương tác: {exc}",
                        file=sys.stderr,
                    )
                    break
                if key == ord("q"):
                    if active_started is not None and active_stats is not None:
                        scenario_results.append(
                            _scenario_summary(
                                scenario,
                                active_stats,
                                "PARTIAL",
                                phase_elapsed,
                            )
                        )
                    break
                if active_started is None:
                    if key == ord("s") and scenario[4]:
                        skipped = _new_scenario_stats()
                        scenario_results.append(
                            _scenario_summary(scenario, skipped, "SKIPPED_BY_USER", 0.0)
                        )
                        scenario_index += 1
                    elif key == ord(" "):
                        active_started = perf_counter()
                        active_stats = _new_scenario_stats()
                elif phase_elapsed >= scenario[2]:
                    assert active_stats is not None
                    scenario_results.append(
                        _scenario_summary(scenario, active_stats, "COMPLETE", phase_elapsed)
                    )
                    scenario_index += 1
                    active_started = None
                    active_stats = None
    except SourceError as exc:
        capture_error = str(exc)
        if active_started is not None and active_stats is not None:
            scenario_results.append(
                _scenario_summary(
                    scenarios[scenario_index],
                    active_stats,
                    "PARTIAL_CAPTURE_ERROR",
                    perf_counter() - active_started,
                )
            )
    finally:
        try:
            cv2.destroyAllWindows()
        except cv2.error:
            pass

    statuses = {str(item["status"]) for item in scenario_results}
    complete = (
        len(scenario_results) == len(scenarios)
        and statuses <= {"COMPLETE", "SKIPPED_BY_USER"}
        and capture_error is None
    )
    return {
        "measurement_status": "COMPLETE" if complete else "PARTIAL",
        "measurement_type": "INTERACTIVE_UNLABELLED_SPOT_CHECK",
        "measured_at_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "camera": {
            "index": args.camera_index,
            "backend": backend_name,
            "requested_resolution": [args.width, args.height],
            "reported_resolution": [capture_width, capture_height],
        },
        "session_duration_seconds": perf_counter() - session_start,
        "scenarios": scenario_results,
        "camera_capture": {
            "read_attempts": source.capture_read_attempts,
            "read_failures": source.capture_failures,
            "failure": capture_error,
        },
        "visualization": display_status,
        "config_hash": config.config_hash,
        "model_sha256": sha256_file(model_path),
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "architecture": platform.machine(),
            "opencv": cv2.__version__,
            "mediapipe": _package_version("mediapipe"),
            "numpy": np.__version__,
        },
        "limitations": (
            "Người tham gia tự bắt đầu từng pha; cue và trạng thái quan sát không "
            "phải ground truth độc lập, không dùng tính accuracy/F1."
        ),
        "privacy": "Không lưu frame, ảnh, đặc trưng, timestamp từng frame hoặc video.",
    }


def run_benchmark(args: argparse.Namespace) -> dict[str, object]:
    config = load_config(args.config)
    model_path = args.model or Path(config.vision.model_path)
    if not model_path.is_file():
        raise LandmarkerError(
            f"Thiếu model Face Landmarker: {model_path}. "
            "Tải bằng `python scripts/download_model.py`."
        )

    processing_ms: list[float] = []
    source_timestamps_s: list[float] = []
    states: Counter[str] = Counter()
    quality_reasons: Counter[str] = Counter()
    face_detected = 0
    accepted_landmarks = 0
    pipeline_valid = 0
    warning_frames = 0
    phase_stats: dict[str, dict[str, object]] = {}
    interrupted = False
    capture_error: str | None = None
    backend_name: str | None = None
    capture_width: float | None = None
    capture_height: float | None = None
    source = VideoSource(
        "camera",
        camera_index=args.camera_index,
        width=args.width,
        height=args.height,
    )
    start = perf_counter()
    with ExitStack() as stack:
        landmarker = stack.enter_context(
            MediaPipeLandmarker(model_path, max_faces=config.vision.num_faces)
        )
        stack.enter_context(source)
        assert source.capture is not None
        try:
            backend_name = source.capture.getBackendName()
        except cv2.error:
            backend_name = None
        try:
            width_value = float(source.capture.get(cv2.CAP_PROP_FRAME_WIDTH))
            height_value = float(source.capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
            capture_width = width_value if width_value > 0 else None
            capture_height = height_value if height_value > 0 else None
        except cv2.error:
            pass
        pipeline = DMSPipeline(landmarker, config)
        start = perf_counter()
        display_enabled = args.guided_scenarios
        while perf_counter() - start < args.duration_seconds:
            try:
                sample = next(source)
            except SourceError as exc:
                capture_error = str(exc)
                break
            result = pipeline.process(sample)
            elapsed_s = perf_counter() - start
            processing_ms.append(result.processing_ms)
            source_timestamps_s.append(sample.timestamp_s)
            face_detected += int(result.face_detected)
            accepted_landmarks += int(result.face_landmarks is not None)
            pipeline_valid += int(result.quality_valid)
            warning_frames += int(result.snapshot.warning)
            states[result.state.value] += 1
            quality_reasons[result.quality_reason or "valid"] += 1
            phase = next(
                (
                    phase
                    for phase in GUIDED_PHASES
                    if phase[0] <= elapsed_s < phase[1]
                ),
                None,
            )
            if phase is not None:
                _, _, key, _, _ = phase
                stats = phase_stats.setdefault(
                    key,
                    {
                        "requested_action": phase[3],
                        "expected_state_hypothesis": phase[4],
                        "frames": 0,
                        "face_detected_frames": 0,
                        "pipeline_valid_frames": 0,
                        "warning_frames": 0,
                        "observed_states": Counter(),
                    },
                )
                stats["frames"] = int(stats["frames"]) + 1
                stats["face_detected_frames"] = int(stats["face_detected_frames"]) + int(
                    result.face_detected
                )
                stats["pipeline_valid_frames"] = int(
                    stats["pipeline_valid_frames"]
                ) + int(result.quality_valid)
                stats["warning_frames"] = int(stats["warning_frames"]) + int(
                    result.snapshot.warning
                )
                observed_states = stats["observed_states"]
                assert isinstance(observed_states, Counter)
                observed_states[result.state.value] += 1
                if display_enabled:
                    try:
                        display = draw_overlay(
                            sample.frame,
                            result,
                            (len(processing_ms) / max(elapsed_s, 1e-6)),
                            mirror=config.display.mirror,
                        )
                        cv2.putText(
                            display,
                            f"SCENARIO {key.upper()}: {phase[3]}",
                            (12, 25),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.55,
                            (255, 255, 255),
                            2,
                            cv2.LINE_AA,
                        )
                        cv2.imshow("VinFast DMS · Kiểm tra tình huống", display)
                        if cv2.waitKey(1) & 0xFF == ord("q"):
                            interrupted = True
                            break
                    except cv2.error as exc:
                        display_enabled = False
                        print(
                            f"Không mở được cửa sổ; tiếp tục headless: {exc}",
                            file=sys.stderr,
                        )
        elapsed_s = perf_counter() - start

    if args.guided_scenarios:
        try:
            cv2.destroyAllWindows()
        except cv2.error:
            pass
    frame_count = len(processing_ms)
    processing_s = sum(processing_ms) / 1000.0
    source_span_s = (
        source_timestamps_s[-1] - source_timestamps_s[0]
        if len(source_timestamps_s) > 1
        else 0.0
    )
    capture_attempts = source.capture_read_attempts
    capture_failures = source.capture_failures
    return {
        "measurement_status": (
            "COMPLETE"
            if frame_count and not capture_error and not interrupted
            else "PARTIAL"
        ),
        "measured_at_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "camera": {
            "index": args.camera_index,
            "backend": backend_name,
            "requested_resolution": [args.width, args.height],
            "reported_resolution": [capture_width, capture_height],
        },
        "duration_seconds": elapsed_s,
        "processed_frames": frame_count,
        "camera_source_fps": (
            (frame_count - 1) / source_span_s if source_span_s > 0.0 else None
        ),
        "pipeline_processing_capacity_fps": (
            frame_count / processing_s if processing_s else None
        ),
        "headless_throughput_fps": frame_count / elapsed_s if elapsed_s else None,
        "processing_latency_ms": {
            "mean": float(np.mean(processing_ms)) if processing_ms else None,
            "p50": _percentile(processing_ms, 50),
            "p95": _percentile(processing_ms, 95),
            "definition": (
                "Thời gian trong DMSPipeline.process; không gồm chờ camera "
                "hoặc vẽ màn hình."
            ),
        },
        "landmarks": {
            "face_detected_frames": face_detected,
            "face_detection_rate": face_detected / frame_count if frame_count else None,
            "landmark_quality_gate_passed_frames": accepted_landmarks,
            "landmark_quality_gate_rate": (
                accepted_landmarks / frame_count if frame_count else None
            ),
            "pipeline_valid_frames": pipeline_valid,
            "pipeline_valid_rate": pipeline_valid / frame_count if frame_count else None,
        },
        "quality_reasons": dict(sorted(quality_reasons.items())),
        "camera_capture": {
            "read_attempts": capture_attempts,
            "read_failures": capture_failures,
            "failure_rate": (
                capture_failures / capture_attempts if capture_attempts else None
            ),
            "failure": capture_error,
        },
        "states": dict(sorted(states.items())),
        "warning_frames": warning_frames,
        "guided_scenario_check": (
            {
                "status": "UNLABELLED_SPOT_CHECK",
                "visualization": "DISPLAYED" if display_enabled else "UNAVAILABLE",
                "phases": {
                    key: {
                        **{
                            name: value
                            for name, value in stats.items()
                            if name != "observed_states"
                        },
                        "observed_states": dict(sorted(stats["observed_states"].items())),
                        "face_detection_rate": (
                            int(stats["face_detected_frames"]) / int(stats["frames"])
                            if int(stats["frames"])
                            else None
                        ),
                        "pipeline_valid_rate": (
                            int(stats["pipeline_valid_frames"]) / int(stats["frames"])
                            if int(stats["frames"])
                            else None
                        ),
                    }
                    for key, stats in sorted(phase_stats.items())
                },
                "interpretation": (
                    "Cue mô tả hành vi được yêu cầu, không phải ground truth đã "
                    "xác nhận độc lập; không dùng để tính accuracy hoặc F1."
                ),
            }
            if args.guided_scenarios
            else None
        ),
        "camera_to_display_latency_ms": None,
        "camera_to_display_note": "N/A: đo headless, không có pipeline màn hình để định thời.",
        "event_to_warning_latency_s": None,
        "event_to_warning_note": "N/A: chưa có sự kiện được gắn nhãn độc lập.",
        "evaluation_metrics": {
            "precision_recall_f1": None,
            "false_alarms_per_minute": None,
            "note": "N/A: không có ground truth được gắn nhãn.",
        },
        "config_hash": config.config_hash,
        "model_sha256": sha256_file(model_path),
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "architecture": platform.machine(),
            "processor": platform.processor() or None,
            "opencv": cv2.__version__,
            "mediapipe": _package_version("mediapipe"),
            "numpy": np.__version__,
        },
        "privacy": "Không lưu frame, ảnh, đặc trưng, timestamp từng frame hoặc video.",
    }


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.duration_seconds <= 0:
        parser.error("--duration-seconds phải lớn hơn 0.")
    if args.width < 1 or args.height < 1:
        parser.error("--width và --height phải lớn hơn 0.")
    if args.guided_scenarios and args.duration_seconds != 60.0:
        parser.error("--guided-scenarios cần --duration-seconds 60.")
    if args.guided_scenarios and args.interactive_scenarios:
        parser.error("Chỉ chọn một trong --guided-scenarios hoặc --interactive-scenarios.")
    if args.scenario and not args.interactive_scenarios:
        parser.error("--scenario chỉ dùng cùng --interactive-scenarios.")
    try:
        report = (
            run_interactive_scenario_check(args)
            if args.interactive_scenarios
            else run_benchmark(args)
        )
    except (LandmarkerError, SourceError, OSError, ValueError, cv2.error) as exc:
        print(f"BENCHMARK FAILED: {exc}", file=sys.stderr)
        return 2
    serialized = json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False)
    if args.output is not None:
        output = args.output.expanduser()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(serialized + "\n", encoding="utf-8")
        print(f"Đã lưu JSON thống kê (không có dữ liệu ảnh/video): {output}")
    print(serialized)
    return 0 if report["measurement_status"] == "COMPLETE" else 3


if __name__ == "__main__":
    raise SystemExit(main())
