from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any


MAX_ARTIFACT_BYTES = 2 * 1024 * 1024
RUN_ID = re.compile(r"^[a-z0-9](?:[a-z0-9]|-(?=[a-z0-9])){0,95}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
REQUIRED_ARTIFACTS = (
    "meta.json",
    "ROUTE.json",
    "DISPATCH.json",
    "VERDICT.json",
    "OUTCOME.json",
)


class AdapterError(ValueError):
    """Raised when a Sync run cannot be safely imported."""


def canonical_json(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def fingerprint(value: object) -> str:
    return hashlib.sha256(canonical_json(value)).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AdapterError(message)


def load_artifact(run_dir: Path, name: str) -> dict[str, Any]:
    path = run_dir / name
    require(not path.is_symlink(), f"{name} may not be a symlink")
    require(path.is_file(), f"missing required artifact: {name}")
    require(path.stat().st_size <= MAX_ARTIFACT_BYTES, f"artifact too large: {name}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise AdapterError(f"invalid JSON in {name}: {exc}") from exc
    require(isinstance(value, dict), f"{name} must contain an object")
    return value


def text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise AdapterError(f"missing or invalid {label}")
    return value


def load_run(value: str | Path) -> dict[str, Any]:
    requested = Path(value).expanduser()
    require(not requested.is_symlink(), "run directory may not be a symlink")
    try:
        run_dir = requested.resolve(strict=True)
    except FileNotFoundError as exc:
        raise AdapterError(f"run directory does not exist: {requested}") from exc
    require(run_dir.is_dir(), f"run path is not a directory: {run_dir}")

    artifacts = {name: load_artifact(run_dir, name) for name in REQUIRED_ARTIFACTS}
    meta = artifacts["meta.json"]
    route = artifacts["ROUTE.json"]
    dispatch = artifacts["DISPATCH.json"]
    verdict = artifacts["VERDICT.json"]
    outcome = artifacts["OUTCOME.json"]

    run_id = text(meta.get("run_id"), "meta.run_id")
    require(RUN_ID.fullmatch(run_id) is not None, "invalid run id")
    require(run_dir.name == run_id, "run directory name does not match meta.run_id")
    project = text(meta.get("project"), "meta.project")
    role = text(route.get("role"), "route.role")
    pool = text(route.get("pool"), "route.pool")

    require(route.get("run_id") == run_id, "route is not bound to this run")
    require(route.get("project") == project, "route project does not match metadata")
    route_fingerprint = fingerprint(route)
    require(dispatch.get("run_id") == run_id, "dispatch is not bound to this run")
    require(
        dispatch.get("project") == project, "dispatch project does not match metadata"
    )
    require(
        dispatch.get("route_fingerprint") == route_fingerprint,
        "dispatch route fingerprint mismatch",
    )
    config = dispatch.get("config")
    require(isinstance(config, dict), "dispatch config must be an object")
    config_fingerprint = fingerprint(config)
    require(
        dispatch.get("config_fingerprint") == config_fingerprint,
        "dispatch config fingerprint mismatch",
    )
    dispatch_fingerprint = fingerprint(dispatch)
    require(
        verdict.get("project") == project, "verdict project does not match metadata"
    )
    require(
        verdict.get("dispatch_attempt_id") == dispatch.get("attempt_id"),
        "verdict dispatch attempt mismatch",
    )
    require(
        verdict.get("dispatch_fingerprint") == dispatch_fingerprint,
        "verdict dispatch fingerprint mismatch",
    )

    require(outcome.get("run_id") == run_id, "outcome is not bound to this run")
    require(
        outcome.get("project") == project, "outcome project does not match metadata"
    )
    require(outcome.get("role") == role, "outcome role does not match route")
    require(outcome.get("pool") == pool, "outcome pool does not match route")
    require(
        outcome.get("route_fingerprint") == route_fingerprint,
        "outcome route fingerprint mismatch",
    )
    require(
        outcome.get("dispatch_fingerprint") == dispatch_fingerprint,
        "outcome dispatch fingerprint mismatch",
    )
    require(
        outcome.get("dispatch_config_fingerprint") == config_fingerprint,
        "outcome dispatch config fingerprint mismatch",
    )
    require(
        outcome.get("gate_status") == verdict.get("status"),
        "outcome gate status does not match verdict",
    )
    require(
        outcome.get("gate_passed") == verdict.get("passed"),
        "outcome gate boolean does not match verdict",
    )

    result_path = run_dir / "RESULT.json"
    result: dict[str, Any] | None = None
    if result_path.exists() or result_path.is_symlink():
        result = load_artifact(run_dir, "RESULT.json")
        require(
            dispatch.get("result_sha256") == fingerprint(result),
            "result fingerprint mismatch",
        )
        require(
            dispatch.get("executor_status") == result.get("status"),
            "result status does not match dispatch",
        )
    elif dispatch.get("result_status") == "valid":
        raise AdapterError(
            "dispatch declares a valid result but RESULT.json is missing"
        )

    steps = verdict.get("steps")
    if not isinstance(steps, list):
        raise AdapterError("verdict steps must be an array")
    safe_steps: list[dict[str, Any]] = []
    for index, step in enumerate(steps, start=1):
        require(isinstance(step, dict), f"verdict step {index} must be an object")
        step_id = text(step.get("id"), f"verdict step {index} id")
        output_sha256 = text(
            step.get("output_sha256"), f"verdict step {index} output hash"
        )
        require(
            SHA256.fullmatch(output_sha256) is not None,
            f"invalid output hash for step {step_id}",
        )
        safe_steps.append(
            {
                "id": step_id,
                "result": text(step.get("result"), f"verdict step {step_id} result"),
                "exit_code": step.get("exit_code"),
                "hard": step.get("hard"),
                "seconds": step.get("seconds"),
                "execution_mode": text(
                    step.get("execution_mode"), f"verdict step {step_id} execution mode"
                ),
                "output_sha256": output_sha256,
            }
        )

    project_name = Path(project).name or "project"
    source_artifacts = [
        {"name": name, "sha256": sha256_file(run_dir / name)}
        for name in REQUIRED_ARTIFACTS
    ]
    if result is not None:
        source_artifacts.append(
            {"name": "RESULT.json", "sha256": sha256_file(result_path)}
        )

    return {
        "schema_version": "sync-run-adapter/1",
        "run_id": run_id,
        "opened_at": text(meta.get("opened_at"), "meta.opened_at"),
        "recorded_at": text(outcome.get("at"), "outcome.at"),
        "project": {
            "name": project_name,
            "path_sha256": hashlib.sha256(project.encode()).hexdigest(),
        },
        "route": {
            "role": role,
            "harness": text(route.get("harness"), "route.harness"),
            "model": text(route.get("model"), "route.model"),
            "effort": text(route.get("effort"), "route.effort"),
            "source_pool": route.get("source_pool"),
            "pool": pool,
            "capacity_status": text(
                route.get("capacity_status"), "route.capacity_status"
            ),
        },
        "execution": {
            "executor_status": outcome.get("executor_status"),
            "dispatch_exit_code": outcome.get("dispatch_exit_code"),
            "result_validation": text(
                outcome.get("result_validation"), "outcome.result_validation"
            ),
            "wall_clock_s": outcome.get("wall_clock_s"),
        },
        "gate": {
            "status": text(verdict.get("status"), "verdict.status"),
            "passed": verdict.get("passed"),
            "steps": safe_steps,
        },
        "outcome": {
            "status": text(outcome.get("outcome_status"), "outcome.outcome_status"),
            "triggers_fired": outcome.get("triggers_fired"),
        },
        "bindings": {
            "route_fingerprint": route_fingerprint,
            "dispatch_fingerprint": dispatch_fingerprint,
            "dispatch_config_fingerprint": config_fingerprint,
        },
        "source_artifacts": source_artifacts,
    }


def render_report(record: dict[str, Any], raw_rel: str) -> str:
    run_id = str(record["run_id"])
    day = str(record["recorded_at"])[:10]
    route = record["route"]
    execution = record["execution"]
    gate = record["gate"]
    outcome = record["outcome"]
    rows = (
        "\n".join(
            f"| `{step['id']}` | {step['result']} | {step['exit_code']} | {step['execution_mode']} | `{step['output_sha256']}` |"
            for step in gate["steps"]
        )
        or "| No gate steps recorded | inconclusive |  |  |  |"
    )
    artifacts = "\n".join(
        f"- `{item['name']}`: `{item['sha256']}`" for item in record["source_artifacts"]
    )
    return f'''---
type: "report"
title: "Sync Run {run_id}"
domain: "Claude and Codex council orchestration"
status: "active"
created: "{day}"
updated: "{day}"
tags:
  - "#domain/claude-and-codex-council-orchestration-task-routing-across-billi"
  - "#type/report"
  - "#confidence/evidence-based"
confidence: "evidence-based"
related:
  - "[[Weekly Report]]"
  - "[[Health Scorecard]]"
source_urls: []
sources:
  - "{raw_rel}"
---

# Sync Run {run_id}

## Recorded Result

- Project label: `{record["project"]["name"]}`
- Role: `{route["role"]}` via `{route["harness"]}`
- Model and effort: `{route["model"]}` at `{route["effort"]}`
- Declared destination pool: `{route["pool"]}`
- Capacity status: `{route["capacity_status"]}`
- Executor status: `{execution["executor_status"]}`
- Gate status: `{gate["status"]}`
- Outcome status: `{outcome["status"]}`
- Wall clock: `{execution["wall_clock_s"]}` seconds

Capacity status is reported from the recorded run. It is not promoted to an
independent capacity claim by this adapter.

## Gate Evidence

| Step | Result | Exit | Mode | Persisted output SHA-256 |
|---|---|---:|---|---|
{rows}

## Artifact Sources

The importer verified the route, dispatch, result when present, verdict, and
outcome bindings before creating this report. Arbitrary executor output and
captured output tails are intentionally excluded.

{artifacts}

- Normalized immutable source: `{raw_rel}`

Related: [[Weekly Report]] | [[Health Scorecard]] | [[Reporting Workflow]]
'''


def atomic_private_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, staged = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
        os.replace(staged, path)
        path.chmod(0o600)
    finally:
        if os.path.exists(staged):
            os.unlink(staged)


def import_run(vault_value: str | Path, run_value: str | Path) -> tuple[Path, Path]:
    vault = Path(vault_value).expanduser().resolve(strict=True)
    require(
        vault.is_dir() and (vault / "CODEX.md").is_file(), f"not a brain vault: {vault}"
    )
    record = load_run(run_value)
    raw_rel = f".raw/sync-runs/{record['run_id']}.json"
    raw_path = vault / raw_rel
    payload = json.dumps(record, indent=2, sort_keys=True).encode() + b"\n"
    if raw_path.exists():
        require(not raw_path.is_symlink(), "normalized raw record may not be a symlink")
        require(
            raw_path.read_bytes() == payload,
            "immutable normalized run already exists with different content",
        )
    else:
        atomic_private_write(raw_path, payload)

    report_path = vault / "wiki" / "reports" / f"Sync Run {record['run_id']}.md"
    report = render_report(record, raw_rel).encode()
    atomic_private_write(report_path, report)
    return raw_path, report_path
