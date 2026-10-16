import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.benchmark import read_manifest

from vinfast_dms.metrics import EvaluationError


def test_benchmark_manifest_resolves_paths_from_manifest_directory(tmp_path: Path) -> None:
    source = tmp_path / "video.avi"
    labels = tmp_path / "labels.csv"
    source.touch()
    labels.touch()
    manifest = tmp_path / "manifest.csv"
    manifest.write_text("source,labels\nvideo.avi,labels.csv\n", encoding="utf-8")

    entries = read_manifest(manifest)

    assert entries == [{"source": source.resolve(), "labels": labels.resolve()}]


def test_benchmark_manifest_requires_existing_pairs(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.csv"
    manifest.write_text("source,labels\nmissing.avi,missing.csv\n", encoding="utf-8")
    with pytest.raises(EvaluationError, match="Không tìm thấy video"):
        read_manifest(manifest)


def test_benchmark_manifest_requires_schema_and_samples(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.csv"
    manifest.write_text("video,truth\na,b\n", encoding="utf-8")
    with pytest.raises(EvaluationError, match="source, labels"):
        read_manifest(manifest)
    manifest.write_text("source,labels\n", encoding="utf-8")
    with pytest.raises(EvaluationError, match="không có video"):
        read_manifest(manifest)


@pytest.mark.parametrize(
    "script",
    [
        "scripts/annotate_events.py",
        "scripts/evaluate.py",
        "scripts/benchmark.py",
        "scripts/reproduce_failure.py",
    ],
)
def test_evaluation_tools_help(script: str) -> None:
    result = subprocess.run(
        [sys.executable, script, "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "--help" in result.stdout
