from dataclasses import replace

import pytest

from vinfast_dms.config import Config, load_config


def test_default_config_loads_and_validates() -> None:
    config = load_config()
    config.validate()
    assert config.thresholds.ear_open > config.thresholds.ear_closed
    assert len(config.config_hash) == 64


def test_invalid_eye_threshold_order_is_rejected() -> None:
    config = Config(thresholds=replace(Config().thresholds, ear_open=0.2))
    with pytest.raises(ValueError, match="ear_closed"):
        config.validate()


def test_invalid_face_count_is_rejected() -> None:
    config = Config(vision=replace(Config().vision, num_faces=0))
    with pytest.raises(ValueError, match="num_faces"):
        config.validate()
