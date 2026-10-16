import numpy as np

from vinfast_dms.overlay import draw_overlay
from vinfast_dms.pipeline import PipelineResult
from vinfast_dms.temporal import DMSState, StateSnapshot


def test_overlay_draws_vietnamese_unknown_banner_in_mirror_mode() -> None:
    result = PipelineResult(
        frame_index=0,
        timestamp_s=0.0,
        face_landmarks=None,
        eye_metrics=None,
        head_pose=None,
        quality_valid=False,
        quality_reason="no_face",
        snapshot=StateSnapshot(0.0, DMSState.UNKNOWN, False, "no_face", None, None, 0.0, 0.0),
        processing_ms=2.5,
    )
    image = draw_overlay(np.zeros((480, 640, 3), dtype=np.uint8), result, 25.0, mirror=True)
    assert image.shape == (480, 640, 3)
    assert image.dtype == np.uint8
    assert image[:120].mean() > image[200:].mean()
