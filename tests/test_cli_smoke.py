import subprocess
import sys


def test_model_downloader_help() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/download_model.py", "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "--output" in result.stdout


def test_camera_check_help_does_not_open_camera() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/check_camera.py", "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "--camera-index" in result.stdout
    assert "--duration-seconds" in result.stdout


def test_demo_cli_help_does_not_require_camera_or_model() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "vinfast_dms", "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "--source" in result.stdout
    assert "--headless" in result.stdout


def test_headless_camera_requires_a_frame_limit_without_opening_camera() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "vinfast_dms", "--source", "camera", "--headless"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 2
    assert "--max-frames" in result.stderr


def test_replay_script_help() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/replay.py", "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "--source" in result.stdout
