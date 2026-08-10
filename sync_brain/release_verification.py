from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


EVIDENCE_REL = Path("references/verification/market-ready.json")
EXCLUDED_PARTS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "venv",
}
EXCLUDED_PREFIXES = (".release-repro-", ".audit-release-")
REQUIRED_CHECKS = {
    "compileall",
    "secret-scan",
    "ruff",
    "mypy",
    "pytest-full",
    "pipeline",
    "demo-byte-tree",
}


def included_files(repo: Path) -> list[Path]:
    files: list[Path] = []
    for path in repo.rglob("*"):
        rel = path.relative_to(repo)
        if rel == EVIDENCE_REL:
            continue
        if any(part in EXCLUDED_PARTS for part in rel.parts):
            continue
        if any(part.endswith(".egg-info") for part in rel.parts):
            continue
        if any(part.startswith(EXCLUDED_PREFIXES) for part in rel.parts):
            continue
        if path.is_symlink():
            raise ValueError(f"release verification refuses symlink: {rel.as_posix()}")
        if path.is_file() and not path.name.endswith((".pyc", ".pyo", ".log")):
            files.append(path)
    return sorted(files, key=lambda item: item.relative_to(repo).as_posix())


def source_tree_fingerprint(repo: Path) -> str:
    digest = hashlib.sha256()
    for path in included_files(repo):
        rel = path.relative_to(repo).as_posix().encode()
        data = path.read_bytes()
        digest.update(len(rel).to_bytes(8, "big"))
        digest.update(rel)
        digest.update(len(data).to_bytes(8, "big"))
        digest.update(data)
    return digest.hexdigest()


def validate_evidence(repo: Path) -> tuple[bool, list[str], dict[str, Any]]:
    path = repo / EVIDENCE_REL
    if not path.is_file() or path.is_symlink():
        return False, [f"missing {EVIDENCE_REL.as_posix()}"], {}
    try:
        evidence = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return False, [f"invalid market-ready evidence: {exc}"], {}
    if (
        not isinstance(evidence, dict)
        or evidence.get("schema") != "sync-market-ready-evidence/1"
    ):
        return False, ["invalid market-ready evidence schema"], {}
    notes: list[str] = []
    try:
        current = source_tree_fingerprint(repo)
    except ValueError as exc:
        return False, [str(exc)], evidence
    if evidence.get("source_tree_sha256") != current:
        notes.append("market-ready evidence is stale for the current source tree")
    checks = evidence.get("checks")
    if not isinstance(checks, list):
        notes.append("market-ready evidence checks must be an array")
        checks = []
    by_name = {
        row.get("name"): row
        for row in checks
        if isinstance(row, dict) and isinstance(row.get("name"), str)
    }
    missing = sorted(REQUIRED_CHECKS - set(by_name))
    if missing:
        notes.append("market-ready evidence missing checks: " + ", ".join(missing))
    failed = sorted(
        name
        for name, row in by_name.items()
        if name in REQUIRED_CHECKS and row.get("exit_code") != 0
    )
    if failed:
        notes.append(
            "market-ready evidence contains failed checks: " + ", ".join(failed)
        )
    return not notes, notes, evidence
