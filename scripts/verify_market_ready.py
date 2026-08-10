#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parent.parent
PY = sys.executable
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from sync_brain.release_verification import (  # noqa: E402
    EVIDENCE_REL,
    source_tree_fingerprint,
)


def safe_argv(argv: list[str]) -> list[str]:
    """Keep reproducible command evidence without persisting user-local paths."""
    repo_text = str(REPO)
    home_text = str(Path.home())
    sanitized: list[str] = []
    for item in argv:
        value = item.replace(repo_text, "<repo>")
        value = value.replace(home_text, "<home>")
        sanitized.append(value)
    return sanitized


def run_check(
    name: str, argv: list[str], *, env: dict[str, str] | None = None
) -> dict[str, Any]:
    print(f"[{name}] {' '.join(argv)}", flush=True)
    proc = subprocess.run(
        argv,
        cwd=REPO,
        text=True,
        capture_output=True,
        env={**os.environ, **(env or {})},
        check=False,
    )
    output = (proc.stdout or "") + (proc.stderr or "")
    if output:
        print(output[-4000:], end="" if output.endswith("\n") else "\n")
    return {
        "name": name,
        "argv": safe_argv(argv),
        "exit_code": proc.returncode,
        "output_sha256": hashlib.sha256(output.encode()).hexdigest(),
    }


def secret_rows(value: object) -> set[tuple[str, str, str]]:
    if not isinstance(value, dict):
        return set()
    results = value.get("results")
    if not isinstance(results, dict):
        return set()
    rows: set[tuple[str, str, str]] = set()
    for filename, findings in results.items():
        if not isinstance(filename, str) or not isinstance(findings, list):
            continue
        for finding in findings:
            if not isinstance(finding, dict):
                continue
            type_ = finding.get("type")
            digest = finding.get("hashed_secret")
            if isinstance(type_, str) and isinstance(digest, str):
                rows.add((filename, type_, digest))
    return rows


def run_secret_check() -> dict[str, Any]:
    command = [
        "detect-secrets",
        "scan",
        "--slim",
        "--all-files",
        "--no-verify",
        "--exclude-files",
        r"(^|/)(dist|\.git|\.mypy_cache|\.pytest_cache|\.ruff_cache|__pycache__)/|^\.secrets\.baseline$|^references/verification/market-ready\.json$",
    ]
    print(f"[secret-scan] {' '.join(command)}", flush=True)
    proc = subprocess.run(
        command,
        cwd=REPO,
        text=True,
        capture_output=True,
        check=False,
    )
    output = (proc.stdout or "") + (proc.stderr or "")
    exit_code = proc.returncode
    summary = ""
    if exit_code == 0:
        try:
            scanned = json.loads(proc.stdout)
            baseline = json.loads(
                (REPO / ".secrets.baseline").read_text(encoding="utf-8")
            )
        except (OSError, ValueError) as exc:
            exit_code = 1
            summary = f"could not parse hashed secret scan: {exc}"
        else:
            extra = secret_rows(scanned) - secret_rows(baseline)
            missing = secret_rows(baseline) - secret_rows(scanned)
            if extra or missing:
                exit_code = 1
                summary = (
                    f"hashed secret baseline mismatch: {len(extra)} new, "
                    f"{len(missing)} missing"
                )
            else:
                summary = f"hashed secret baseline matched {len(secret_rows(scanned))} reviewed findings"
    else:
        summary = "secret scanner could not complete"
    print(summary)
    return {
        "name": "secret-scan",
        "argv": safe_argv(command),
        "exit_code": exit_code,
        "output_sha256": hashlib.sha256(output.encode()).hexdigest(),
        "summary": summary,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Execute and record the source-bound Sync market-ready acceptance suite."
    )
    parser.add_argument(
        "--write-evidence",
        action="store_true",
        help="write references/verification/market-ready.json after every check passes",
    )
    args = parser.parse_args(argv)
    checks: list[dict[str, Any]] = []
    checks.append(
        run_check(
            "compileall",
            [
                PY,
                "-m",
                "compileall",
                "-q",
                "scripts",
                "sync_brain",
                "tests",
                "bin/sync",
                "bin/sync-install",
            ],
        )
    )
    checks.append(run_check("ruff", ["ruff", "check", "."]))
    checks.append(run_check("mypy", ["mypy", "."]))
    checks.append(run_secret_check())
    checks.append(run_check("pytest-full", [PY, "-m", "pytest", "-q"]))
    checks.append(run_check("pipeline", [PY, "tests/test_pipeline.py"]))
    with tempfile.TemporaryDirectory(prefix="sync-market-demo-") as temporary:
        checks.append(
            run_check(
                "demo-byte-tree",
                [
                    PY,
                    "scripts/build_demo_vault.py",
                    "--verify-determinism",
                    "--out-dir",
                    temporary,
                ],
            )
        )
    failed = [row["name"] for row in checks if row["exit_code"] != 0]
    if failed:
        print(
            "ERROR: market-ready verification failed: " + ", ".join(failed),
            file=sys.stderr,
        )
        return 1
    evidence = {
        "schema": "sync-market-ready-evidence/1",
        "verified_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "source_tree_sha256": source_tree_fingerprint(REPO),
        "checks": checks,
        "scope": "Local source-bound acceptance evidence. It does not claim that hosted CI, publication, or deployment ran.",
    }
    if args.write_evidence:
        path = REPO / EVIDENCE_REL
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        path.chmod(0o644)
        print(f"wrote {path}")
    else:
        print(json.dumps(evidence, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
