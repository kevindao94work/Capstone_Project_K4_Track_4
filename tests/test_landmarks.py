from pathlib import Path

import numpy as np
import pytest

from vinfast_dms.landmarks import (
    LandmarkerError,
    MediaPipeLandmarker,
    normalized_to_pixels,
)


def test_normalized_landmarks_convert_to_pixels() -> None:
    points = np.asarray([[0.5, 0.25, -0.1], [1.0, 1.0, 0.2]])
    actual = normalized_to_pixels(points, 640, 480)
    np.testing.assert_allclose(actual, [[320, 120, -0.1], [640, 480, 0.2]])


def test_invalid_dimensions_are_rejected() -> None:
    with pytest.raises(ValueError, match="Chiều rộng"):
        normalized_to_pixels(np.zeros((1, 3)), 0, 480)


def test_missing_model_is_actionable(tmp_path: Path) -> None:
    with pytest.raises(LandmarkerError, match="download_model.py"):
        MediaPipeLandmarker(tmp_path / "missing.task")
