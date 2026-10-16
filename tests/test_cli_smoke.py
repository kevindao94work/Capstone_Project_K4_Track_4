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
