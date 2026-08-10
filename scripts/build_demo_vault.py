#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parent.parent
PY = sys.executable
DEMO_SLUG = "sample-vault"
DEMO_DATE = "2026-01-01"


def run(args: list[str], *, env: dict[str, str]) -> None:
    subprocess.run([PY, *args], cwd=REPO, env=env, check=True)


def build_demo(demo_parent: Path, *, fixed_date: str) -> Path:
    """Build the sample vault from fixed inputs into a clean target directory."""
    demo_parent = demo_parent.resolve()
    demo = demo_parent / DEMO_SLUG
    if demo.exists():
        shutil.rmtree(demo)
    environment = os.environ.copy()
    environment["SYNC_DEMO_DATE"] = fixed_date
    run(
        [
            "scripts/scaffold_vault.py",
            "--client",
            DEMO_SLUG,
            "--client-name",
            "Sample Client",
            "--owner",
            "Daniel Agrici",
            "--out-dir",
            str(demo_parent),
        ],
        env=environment,
    )
    run(
        [
            "scripts/ingest_source.py",
            "--vault",
            str(demo),
            "--file",
            "tests/fixtures/sample-source.md",
            "--source-type",
            "fixture",
        ],
        env=environment,
    )
    run(["scripts/synthesize_brain.py", "--vault", str(demo)], env=environment)
    run(
        ["scripts/generate_vault_visuals.py", "--vault", str(demo)],
        env=environment,
    )
    run(
        ["scripts/render_brain_report.py", "--vault", str(demo), "--html-only"],
        env=environment,
    )
    run(["scripts/lint_vault.py", "--vault", str(demo)], env=environment)
    return demo


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def tree_manifest(root: Path) -> dict[str, Any]:
    """Return an ordered byte-level manifest, excluding filesystem metadata."""
    directories: list[str] = []
    files: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        if path.is_symlink():
            raise RuntimeError(f"demo output contains a symlink: {relative}")
        if path.is_dir():
            directories.append(relative)
        elif path.is_file():
            files[relative] = sha256_file(path)
        else:
            raise RuntimeError(f"demo output contains an unsupported entry: {relative}")
    return {"directories": directories, "files": files}


def compare_clean_builds(*, fixed_date: str) -> dict[str, Any]:
    """Build twice in isolated directories and fail if either tree or bytes differ."""
    with tempfile.TemporaryDirectory(prefix="sync-demo-determinism-") as temporary:
        root = Path(temporary)
        first = build_demo(root / "first", fixed_date=fixed_date)
        second = build_demo(root / "second", fixed_date=fixed_date)
        first_manifest = tree_manifest(first)
        second_manifest = tree_manifest(second)
    if first_manifest != second_manifest:
        raise RuntimeError(
            "deterministic demo verification failed: clean builds have different trees or bytes"
        )
    return {
        "fixed_date": fixed_date,
        "directories": len(first_manifest["directories"]),
        "files": len(first_manifest["files"]),
        "tree_sha256": hashlib.sha256(
            json.dumps(first_manifest, sort_keys=True, separators=(",", ":")).encode(
                "utf-8"
            )
        ).hexdigest(),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build the fixed-input Sync demo vault."
    )
    parser.add_argument("--out-dir", default=str(REPO / "examples"))
    parser.add_argument("--fixed-date", default=DEMO_DATE)
    parser.add_argument(
        "--verify-determinism",
        action="store_true",
        help="compare two isolated fixed-input builds before producing the demo",
    )
    args = parser.parse_args(argv)
    try:
        # Validate before running subprocesses so a bad clock cannot partially rebuild output.
        datetime.date.fromisoformat(args.fixed_date)
        if args.verify_determinism:
            print(
                json.dumps(
                    compare_clean_builds(fixed_date=args.fixed_date), sort_keys=True
                )
            )
        demo = build_demo(Path(args.out_dir), fixed_date=args.fixed_date)
    except (OSError, RuntimeError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(demo)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
