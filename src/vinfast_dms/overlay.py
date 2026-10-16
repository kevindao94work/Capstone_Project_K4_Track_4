"""Vẽ trạng thái và đặc trưng bằng văn bản tiếng Việt có dấu."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from vinfast_dms.geometry import LEFT_EYE_INDICES, RIGHT_EYE_INDICES
from vinfast_dms.landmarks import normalized_to_pixels
from vinfast_dms.pipeline import PipelineResult
from vinfast_dms.temporal import STATE_LABELS_VI, DMSState

REASON_LABELS_VI = {
    "no_face": "Không thấy khuôn mặt",
    "multiple_faces": "Có nhiều khuôn mặt trong khung",
    "face_too_small": "Khuôn mặt quá nhỏ",
    "invalid_landmark_shape": "Cấu trúc mốc khuôn mặt không hợp lệ",
    "non_finite_landmarks": "Mốc khuôn mặt không hữu hạn",
    "landmarks_out_of_bounds": "Mốc khuôn mặt ngoài khung ảnh",
    "missing_eye_landmarks": "Thiếu mốc hai mắt",
    "non_finite_eye_landmarks": "Mốc mắt không hợp lệ",
    "zero_eye_width": "Khoảng cách ngang mắt bằng không",
    "implausible_ear": "Tỷ lệ mắt bất hợp lý",
    "solvepnp_failed": "Không ước lượng được tư thế đầu",
    "high_reprojection_error": "Sai số hình học quá lớn",
    "time_gap": "Khoảng cách giữa khung hình quá dài",
    "invalid_timestamp": "Dấu thời gian không hợp lệ",
}


@lru_cache(maxsize=8)
def _font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = (
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Verdana.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "C:/Windows/Fonts/arial.ttf",
    )
    for candidate in candidates:
        if Path(candidate).is_file():
            return ImageFont.truetype(candidate, size=size)
    return ImageFont.load_default()


def _display_points(landmarks: np.ndarray, width: int, height: int, mirror: bool) -> np.ndarray:
    points = normalized_to_pixels(landmarks, width, height)
    if mirror:
        points[:, 0] = width - 1 - points[:, 0]
    return points


def draw_overlay(
    frame: np.ndarray,
    result: PipelineResult,
    fps: float,
    mirror: bool = False,
) -> np.ndarray:
    """Tạo frame hiển thị; ảnh gốc và tính toán không bị mirror."""
    output = cv2.flip(frame, 1) if mirror else frame.copy()
    height, width = output.shape[:2]
    color = {
        DMSState.NORMAL: (38, 145, 87),
        DMSState.EYES_CLOSED: (42, 48, 220),
        DMSState.DISTRACTED: (0, 112, 225),
        DMSState.UNKNOWN: (24, 143, 190),
    }[result.state]
    if result.face_landmarks is not None and result.quality_valid:
        points = _display_points(result.face_landmarks, width, height, mirror)
        finite = np.isfinite(points[:, :2]).all(axis=1)
        face = points[finite, :2]
        if len(face):
            low = np.floor(face.min(axis=0)).astype(int)
            high = np.ceil(face.max(axis=0)).astype(int)
            x0, y0 = np.maximum(low, [0, 0])
            x1, y1 = np.minimum(high, [width - 1, height - 1])
            cv2.rectangle(output, (x0, y0), (x1, y1), (0, 220, 255), 2)
        for indices in (LEFT_EYE_INDICES, RIGHT_EYE_INDICES):
            for index in indices:
                x, y = np.rint(points[index, :2]).astype(int)
                if 0 <= x < width and 0 <= y < height:
                    cv2.circle(output, (x, y), 2, (255, 210, 0), -1)

    rgb = cv2.cvtColor(output, cv2.COLOR_BGR2RGB)
    image = Image.fromarray(rgb)
    draw = ImageDraw.Draw(image, "RGB")
    draw.rectangle((0, 0, width, 122), fill=(14, 25, 38))
    draw.rectangle((0, 0, 12, 122), fill=color)
    draw.text((24, 10), STATE_LABELS_VI[result.state], font=_font(26), fill=(255, 255, 255))
    eyes = result.eye_metrics
    pose = result.head_pose
    ear_text = "—" if eyes is None or eyes.ear_mean is None else f"{eyes.ear_mean:.3f}"
    yaw_text = "—" if pose is None or pose.yaw_deg is None else f"{pose.yaw_deg:+.1f}°"
    pitch_text = "—" if pose is None or pose.pitch_deg is None else f"{pose.pitch_deg:+.1f}°"
    draw.text(
        (24, 49),
        f"EAR: {ear_text}   Yaw: {yaw_text}   Pitch: {pitch_text}",
        font=_font(18),
        fill=(231, 238, 246),
    )
    validity = "Hợp lệ" if result.quality_valid else "Không xác định"
    reason = REASON_LABELS_VI.get(result.quality_reason or "", result.quality_reason or "")
    detail = validity if not reason else f"{validity} · {reason}"
    draw.text((24, 78), detail, font=_font(16), fill=(255, 205, 145))
    draw.text(
        (24, 101),
        f"FPS: {fps:.1f}   Độ trễ: {result.processing_ms:.1f} ms",
        font=_font(15),
        fill=(195, 210, 226),
    )
    return cv2.cvtColor(np.asarray(image), cv2.COLOR_RGB2BGR)
