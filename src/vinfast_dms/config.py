"""Tải và kiểm tra cấu hình hệ thống."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True, slots=True)
class ThresholdConfig:
    ear_closed: float = 0.21
    ear_open: float = 0.24
    yaw_distracted_deg: float = 30.0
    yaw_return_hysteresis_deg: float = 5.0
    closed_hold_s: float = 1.2
    distracted_hold_s: float = 1.0
    max_gap_s: float = 0.75
    ema_tau_s: float = 0.15


@dataclass(frozen=True, slots=True)
class VisionConfig:
    model_path: str = "models/face_landmarker.task"
    num_faces: int = 2
    min_face_fraction: float = 0.08
    max_reprojection_error_px: float = 12.0


@dataclass(frozen=True, slots=True)
class DisplayConfig:
    mirror: bool = True
    width: int = 640
    height: int = 480


@dataclass(frozen=True, slots=True)
class AppConfig:
    language: str = "vi"
    prototype_notice: str = "Mẫu thử hỗ trợ quan sát; không dùng khi lái xe thực tế."


@dataclass(frozen=True, slots=True)
class Config:
    app: AppConfig = AppConfig()
    vision: VisionConfig = VisionConfig()
    thresholds: ThresholdConfig = ThresholdConfig()
    display: DisplayConfig = DisplayConfig()

    def validate(self) -> None:
        t = self.thresholds
        if not 0.0 < t.ear_closed < t.ear_open < 1.0:
            raise ValueError("Cần 0 < ear_closed < ear_open < 1.")
        if not 0.0 < t.yaw_distracted_deg <= 90.0:
            raise ValueError("yaw_distracted_deg phải nằm trong (0, 90].")
        if not 0.0 <= t.yaw_return_hysteresis_deg < t.yaw_distracted_deg:
            raise ValueError("Hysteresis yaw phải không âm và nhỏ hơn ngưỡng yaw.")
        for name in ("closed_hold_s", "distracted_hold_s", "max_gap_s", "ema_tau_s"):
            if getattr(t, name) <= 0.0:
                raise ValueError(f"{name} phải lớn hơn 0.")
        v = self.vision
        if v.num_faces < 1:
            raise ValueError("num_faces phải lớn hơn hoặc bằng 1.")
        if not 0.0 < v.min_face_fraction <= 1.0:
            raise ValueError("min_face_fraction phải nằm trong (0, 1].")
        if v.max_reprojection_error_px <= 0.0:
            raise ValueError("max_reprojection_error_px phải lớn hơn 0.")
        if self.display.width < 1 or self.display.height < 1:
            raise ValueError("Kích thước hiển thị phải là số nguyên dương.")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @property
    def config_hash(self) -> str:
        encoded = json.dumps(self.to_dict(), sort_keys=True, ensure_ascii=False).encode()
        return sha256(encoded).hexdigest()


def load_config(path: str | Path | None = None) -> Config:
    """Đọc YAML; cấu hình thiếu trường sẽ nhận giá trị mặc định."""
    if path is None:
        path = Path(__file__).resolve().parents[2] / "config" / "default.yaml"
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    config = Config(
        app=AppConfig(**raw.get("app", {})),
        vision=VisionConfig(**raw.get("vision", {})),
        thresholds=ThresholdConfig(**raw.get("thresholds", {})),
        display=DisplayConfig(**raw.get("display", {})),
    )
    config.validate()
    return config
