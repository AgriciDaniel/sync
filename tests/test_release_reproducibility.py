from __future__ import annotations

import hashlib
import importlib.util
import os
import shutil
import subprocess
import sys
import uuid
import zipfile
from pathlib import Path

import pytest


REPO = Path(__file__).resolve().parent.parent
PACKAGE_SCRIPT = REPO / "scripts" / "package_release.py"


def load_package_release():
    spec = importlib.util.spec_from_file_location(
        "package_release_test", PACKAGE_SCRIPT
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_package(dist_dir: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(PACKAGE_SCRIPT),
            "--version",
            "0.1.0",
            "--dist-dir",
            str(dist_dir),
        ],
        cwd=REPO,
        text=True,
        capture_output=True,
        env={**os.environ, "SOURCE_DATE_EPOCH": "315532800"},
        check=False,
    )


def test_custom_dist_dir_is_excluded_and_release_bytes_are_reproducible() -> None:
    dist = REPO / f".release-repro-{uuid.uuid4().hex}"
    try:
        first = run_package(dist)
        assert first.returncode == 0, first.stderr
        tracked = sorted(path for path in dist.iterdir() if path.is_file())
        first_bytes = {path.name: sha256(path) for path in tracked}

        second = run_package(dist)
        assert second.returncode == 0, second.stderr
        second_bytes = {path.name: sha256(path) for path in tracked}
        assert second_bytes == first_bytes

        source_zip = dist / "sync-brain-source-v0.1.0.zip"
        with zipfile.ZipFile(source_zip) as archive:
            names = archive.namelist()
            assert all(dist.name not in name for name in names)
            assert {item.date_time for item in archive.infolist()} == {
                (1980, 1, 1, 0, 0, 0)
            }
            raw_names = [name for name in names if "/.raw/" in name]
            assert raw_names
            assert all(
                "/assets/template-brain/.raw/" in name
                or "/examples/sample-vault/.raw/" in name
                for name in raw_names
            )
    finally:
        shutil.rmtree(dist, ignore_errors=True)


def test_invalid_git_directory_falls_back_to_a_tree_and_has_no_commit(
    tmp_path: Path,
) -> None:
    package_release = load_package_release()
    (tmp_path / ".git").mkdir()
    (tmp_path / "README.md").write_text("release input\n", encoding="utf-8")
    original_repo = package_release.REPO
    package_release.REPO = tmp_path
    try:
        assert package_release.has_working_git_checkout() is False
        assert package_release.git_commit() is None
        assert package_release.source_files() == [tmp_path / "README.md"]
    finally:
        package_release.REPO = original_repo


def test_git_checkout_excludes_a_custom_untracked_dist_dir(tmp_path: Path) -> None:
    package_release = load_package_release()
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    (tmp_path / "README.md").write_text("release input\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=tmp_path, check=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=Sync test",
            "-c",
            "user.email=sync-test@example.invalid",
            "commit",
            "-qm",
            "baseline",
        ],
        cwd=tmp_path,
        check=True,
    )
    custom_dist = tmp_path / "release-output"
    custom_dist.mkdir()
    (custom_dist / "artifact.zip").write_bytes(b"not release input")
    original_repo = package_release.REPO
    package_release.REPO = tmp_path
    try:
        assert package_release.source_files(exclude_roots=[custom_dist]) == [
            tmp_path / "README.md"
        ]
    finally:
        package_release.REPO = original_repo


def test_zip_writer_has_stable_metadata_and_order(tmp_path: Path) -> None:
    package_release = load_package_release()
    source = tmp_path / "source"
    source.mkdir()
    (source / "z.txt").write_text("z\n", encoding="utf-8")
    (source / "a.txt").write_text("a\n", encoding="utf-8")
    first = tmp_path / "first.zip"
    second = tmp_path / "second.zip"

    package_release.build_zip(first, source, "fixture")
    package_release.build_zip(second, source, "fixture")

    assert sha256(first) == sha256(second)
    with zipfile.ZipFile(first) as archive:
        assert archive.namelist() == ["fixture/a.txt", "fixture/z.txt"]
        assert {item.date_time for item in archive.infolist()} == {
            (1980, 1, 1, 0, 0, 0)
        }


def test_public_package_rejects_unapproved_raw_material(tmp_path: Path) -> None:
    package_release = load_package_release()
    source = tmp_path / "source"
    raw = source / ".raw"
    raw.mkdir(parents=True)
    (raw / "client.txt").write_text("private client material\n", encoding="utf-8")

    with pytest.raises(SystemExit, match="raw release entry is outside"):
        package_release.build_zip(tmp_path / "unsafe.zip", source, "unsafe")
