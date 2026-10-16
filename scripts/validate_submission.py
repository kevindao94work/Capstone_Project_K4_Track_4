#!/usr/bin/env python3
"""Kiểm tra tài liệu, quyền riêng tư và đồng bộ trước khi nộp repository."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUTHOR_MARKERS = ("Đào Gia Bảo", "2A202602793")
REQUIRED_FILES = (
    "README.md",
    "pyproject.toml",
    "requirements.txt",
    ".gitignore",
    "config/default.yaml",
    "scripts/download_model.py",
    "scripts/check_environment.py",
    "scripts/check_camera.py",
    "scripts/annotate_events.py",
    "scripts/evaluate.py",
    "scripts/benchmark.py",
    "scripts/reproduce_failure.py",
    "scripts/validate_submission.py",
    "src/vinfast_dms/cli.py",
    "src/vinfast_dms/metrics.py",
    "tests/test_geometry.py",
    "tests/test_temporal.py",
    "tests/test_uncertainty.py",
    "tests/test_sources.py",
    "tests/test_logging.py",
    "tests/test_metrics.py",
    "tests/test_cli_smoke.py",
    "docs/BAO_CAO_KY_THUAT.md",
    "docs/PHUONG_PHAP_DANH_GIA.md",
    "docs/KET_QUA_THUC_NGHIEM.md",
    "docs/PHAN_TICH_CA_LOI.md",
    "docs/QUYEN_RIENG_TU_VA_GIOI_HAN.md",
    "docs/GHI_NHAN_CHECKPOINT.md",
    "docs/KICH_BAN_DEMO_10_PHUT.md",
    "docs/CAU_HOI_PHAN_BIEN.md",
    "docs/CHECKLIST_NOP_BAI.md",
)
DOC_FILES = (ROOT / "README.md", *sorted((ROOT / "docs").glob("*.md")))
PLACEHOLDER_PATTERN = re.compile(r"\b(?:TODO|TBD)\b|\bxx\s*%", re.IGNORECASE)
SECRET_PATTERNS = (
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{30,}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{30,}\b"),
    re.compile(
        r"(?i)\b(?:api[_-]?key|access[_-]?token|client[_-]?secret)\b"
        r"\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{24,}"
    ),
)
MEDIA_SUFFIXES = {".mp4", ".mov", ".avi", ".m4v", ".webm"}


def _run_git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def _tracked_paths() -> list[str]:
    result = _run_git("ls-files", "-z")
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "Không đọc được danh sách file Git.")
    return [item for item in result.stdout.split("\0") if item]


def _private_or_sensitive(path: str) -> bool:
    normalized = path.replace("\\", "/")
    basename = Path(path).name.lower()
    if normalized.startswith(("data/private/", "outputs/private/", ".venv/")):
        return basename != "readme.md"
    if basename == ".env" or basename.startswith(".env."):
        return basename != ".env.example"
    if Path(path).suffix.lower() in MEDIA_SUFFIXES | {".task", ".tflite", ".pem", ".key"}:
        return True
    return False


def _relative_markdown_targets(path: Path) -> list[str]:
    targets = re.findall(r"\[[^\]]*\]\(([^)]+)\)", path.read_text(encoding="utf-8"))
    missing: list[str] = []
    for target in targets:
        if target.startswith(("https://", "http://", "mailto:", "#")):
            continue
        local_name = target.split("#", 1)[0]
        if local_name and not (path.parent / local_name).resolve().exists():
            missing.append(f"{path.relative_to(ROOT)} -> {target}")
    return missing


def _ignored(path: str) -> bool:
    result = _run_git("check-ignore", "--quiet", "--no-index", "--", path)
    return result.returncode == 0


def _check_sync() -> tuple[bool, str]:
    branch = _run_git("branch", "--show-current")
    if branch.returncode != 0 or not branch.stdout.strip():
        return False, "Không xác định được branch hiện tại."
    name = branch.stdout.strip()
    local = _run_git("rev-parse", "HEAD")
    remote = _run_git("rev-parse", f"refs/remotes/origin/{name}")
    if local.returncode != 0 or remote.returncode != 0:
        return False, f"Thiếu SHA local hoặc origin/{name}; cần fetch và push."
    if local.stdout.strip() != remote.stdout.strip():
        return False, f"SHA local khác origin/{name}."
    return True, f"{name} local = origin/{name} = {local.stdout.strip()}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--allow-dirty",
        action="store_true",
        help="Cho phép sửa đổi cục bộ khi kiểm tra trước commit.",
    )
    parser.add_argument(
        "--skip-sync",
        action="store_true",
        help="Bỏ kiểm tra SHA remote khi chưa push commit cuối.",
    )
    args = parser.parse_args(argv)
    checks: list[tuple[str, bool, str]] = []

    missing_files = [name for name in REQUIRED_FILES if not (ROOT / name).is_file()]
    checks.append(("Tệp bắt buộc", not missing_files, ", ".join(missing_files) or "đủ"))

    identity_errors = []
    for path in DOC_FILES:
        content = path.read_text(encoding="utf-8")
        if any(marker not in content for marker in AUTHOR_MARKERS):
            identity_errors.append(str(path.relative_to(ROOT)))
    checks.append(
        (
            "Tác giả/MSSV trong README và báo cáo",
            not identity_errors,
            ", ".join(identity_errors) or "thống nhất",
        )
    )

    placeholder_hits = []
    broken_links = []
    for path in DOC_FILES:
        content = path.read_text(encoding="utf-8")
        if PLACEHOLDER_PATTERN.search(content):
            placeholder_hits.append(str(path.relative_to(ROOT)))
        broken_links.extend(_relative_markdown_targets(path))
    checks.append(
        (
            "Placeholder trong tài liệu",
            not placeholder_hits,
            ", ".join(placeholder_hits) or "không có",
        )
    )
    checks.append(
        ("Liên kết Markdown cục bộ", not broken_links, ", ".join(broken_links) or "đều tồn tại")
    )

    try:
        tracked = _tracked_paths()
        forbidden = [path for path in tracked if _private_or_sensitive(path)]
        secret_hits = []
        for relative in tracked:
            file_path = ROOT / relative
            try:
                content = file_path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            if any(pattern.search(content) for pattern in SECRET_PATTERNS):
                secret_hits.append(relative)
        checks.append(
            (
                "Git tracked không có media/private/model/secret",
                not forbidden and not secret_hits,
                ", ".join(forbidden + secret_hits) or f"đã rà {len(tracked)} tệp",
            )
        )
    except (OSError, RuntimeError) as exc:
        checks.append(("Quét Git tracked", False, str(exc)))

    ignore_probes = (
        ".venv/codex-validation-probe",
        "data/private/codex-validation-probe.mp4",
        "outputs/private/codex-validation-probe.csv",
        "models/codex-validation-probe.task",
        "codex-validation-probe.mp4",
        ".env.codex-validation-probe",
    )
    missing_ignore = [path for path in ignore_probes if not _ignored(path)]
    checks.append(
        (
            ".gitignore chặn dữ liệu private/model/media/venv/secrets",
            not missing_ignore,
            ", ".join(missing_ignore) or "các đường dẫn kiểm tra đều bị bỏ qua",
        )
    )

    status = _run_git("status", "--porcelain")
    dirty = status.returncode != 0 or bool(status.stdout.strip())
    dirty_detail = (
        "được phép ở chế độ pre-commit"
        if args.allow_dirty
        else "có thay đổi" if dirty else "sạch"
    )
    checks.append(
        (
            "Working tree sạch",
            args.allow_dirty or not dirty,
            dirty_detail,
        )
    )

    if args.skip_sync:
        checks.append(("Đồng bộ branch origin", True, "được bỏ qua theo tùy chọn"))
    else:
        synced, detail = _check_sync()
        checks.append(("Đồng bộ branch origin", synced, detail))

    failures = 0
    for label, passed, detail in checks:
        print(f"{'PASS' if passed else 'FAIL'} · {label}: {detail}")
        failures += int(not passed)
    if failures:
        print(f"Kiểm tra submission thất bại: {failures} mục.", file=sys.stderr)
        return 1
    print("Kiểm tra submission hoàn tất.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
