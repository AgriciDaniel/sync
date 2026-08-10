#!/usr/bin/env python3
"""Hermetic regression tests for the Sync enforcement harness."""

from __future__ import annotations

import importlib.util
import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys
from importlib.machinery import SourceFileLoader
from pathlib import Path
from types import ModuleType

import pytest
from jsonschema import Draft202012Validator  # type: ignore[import-untyped]

ROOT = Path(__file__).resolve().parents[1]
SYNC = ROOT / "bin" / "sync"
SECRET = "sk-" + "a" * 32  # pragma: allowlist secret


def call(
    tmp_path: Path,
    *args: str,
    cwd: Path | None = None,
    env_extra: dict[str, str] | None = None,
    input_text: str | None = None,
) -> subprocess.CompletedProcess[str]:
    env = {**os.environ, "SYNC_HOME": str(tmp_path / "sync-home")}
    if env_extra:
        env.update(env_extra)
    return subprocess.run(
        [sys.executable, str(SYNC), *args],
        cwd=cwd or tmp_path,
        env=env,
        input=input_text,
        text=True,
        capture_output=True,
        check=False,
    )


def load_harness() -> ModuleType:
    loader = SourceFileLoader("sync_harness_for_test", str(SYNC))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def new_run(tmp_path: Path, project: Path) -> tuple[str, Path]:
    result = call(tmp_path, "run", "new", "safe-run", cwd=project)
    assert result.returncode == 0, result.stderr
    run_id = result.stdout.splitlines()[0].split()[-1]
    return run_id, tmp_path / "sync-home" / "runs" / run_id


def route(
    tmp_path: Path,
    run_id: str,
    project: Path,
    *,
    source_pool: str | None = "claude",
) -> None:
    args = ["route", "--role", "implement", "--run", run_id]
    if source_pool:
        args.extend(["--source-pool", source_pool])
    result = call(tmp_path, *args, cwd=project)
    assert result.returncode == 0, result.stderr


def init_git(project: Path) -> None:
    if not shutil.which("git"):
        pytest.skip("git is required for this harness test")
    proc = subprocess.run(
        ["git", "init", "-q"], cwd=project, text=True, capture_output=True, check=False
    )
    assert proc.returncode == 0, proc.stderr


def project_override(project: Path, steps: list[dict[str, object]]) -> None:
    config = project / ".sync"
    config.mkdir(exist_ok=True)
    (config / "gates.json").write_text(
        json.dumps({"version": 2, "operator_reviewed": True, "steps": steps}),
        encoding="utf-8",
    )


def project_gate_approval(project: Path) -> list[str]:
    raw = (project / ".sync" / "gates.json").read_bytes()
    return [
        "--allow-project-gates",
        "--project-gate-sha256",
        hashlib.sha256(raw).hexdigest(),
    ]


def executable_project_gate_approval(project: Path) -> list[str]:
    """Approve test-only execution when the host has no gate sandbox."""
    return [*project_gate_approval(project), "--allow-unsandboxed-gates"]


def usable_gate_sandbox() -> bool:
    """Require a working sandbox, not merely an installed executable."""
    return bool(
        sys.platform.startswith("linux")
        and load_harness().gate_sandbox_executable()
    )


def fake_codex(tmp_path: Path) -> tuple[Path, dict[str, str]]:
    fake_bin = tmp_path / "fake-bin"
    fake_bin.mkdir()
    executable = fake_bin / "codex"
    executable.write_text(
        f"""#!/usr/bin/env python3
import json
import os
import pathlib
import sys

secret = {SECRET!r}
if "--version" in sys.argv:
    print("codex-cli 0.test")
    raise SystemExit(0)
if len(sys.argv) >= 3 and sys.argv[1:3] == ["login", "status"]:
    print("Logged in using ChatGPT")
    raise SystemExit(0)
mode = os.environ.get("FAKE_CODEX_MODE", "valid")
output = pathlib.Path(sys.argv[sys.argv.index("-o") + 1])
print(json.dumps({{"type": "event", "token": secret, "argv": sys.argv[1:]}}))
print("cookie=" + secret, file=sys.stderr)
if mode == "fail":
    raise SystemExit(7)
if mode == "invalid":
    output.write_text("{{}}", encoding="utf-8")
    raise SystemExit(0)
result = {{
    "schema_version": "sync-result/1",
    "status": "blocked" if mode == "blocked" else "completed",
    "summary": "api_key=" + secret,
    "changed_files": [],
    "checks": [{{"command": "python -m pytest", "exit_code": 0, "result": "pass"}}],
    "unverified": [],
}}
output.write_text(json.dumps(result), encoding="utf-8")
""",
        encoding="utf-8",
    )
    executable.chmod(0o755)
    env = {"PATH": str(fake_bin) + os.pathsep + os.environ.get("PATH", "")}
    return executable, env


@pytest.mark.parametrize(
    "bad", ["../../etc", "/tmp/x", "a/b", "..", "safe run", "a--b"]
)
def test_run_id_rejects_traversal_and_invalid_forms(tmp_path: Path, bad: str) -> None:
    result = call(tmp_path, "run", "show", bad)
    assert result.returncode == 1
    assert "invalid run id" in result.stderr


def test_run_creation_is_unique_bound_and_private(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    first_id, first = new_run(tmp_path, project)
    second_id, _ = new_run(tmp_path, project)
    assert first_id != second_id
    assert stat.S_IMODE((tmp_path / "sync-home").stat().st_mode) == 0o700
    assert stat.S_IMODE(first.stat().st_mode) == 0o700
    assert stat.S_IMODE((first / "EVIDENCE").stat().st_mode) == 0o700
    for artifact in ("meta.json", "BRIEF.md", "WORK_LOG.md"):
        assert stat.S_IMODE((first / artifact).stat().st_mode) == 0o600
    meta = json.loads((first / "meta.json").read_text(encoding="utf-8"))
    assert meta["project"] == str(project.resolve())


def test_run_and_evidence_symlink_escapes_are_rejected(tmp_path: Path) -> None:
    runs = tmp_path / "sync-home" / "runs"
    runs.mkdir(parents=True)
    outside = tmp_path / "outside"
    outside.mkdir()
    (runs / "escape").symlink_to(outside, target_is_directory=True)
    result = call(tmp_path, "run", "show", "escape")
    assert result.returncode == 1
    assert "escapes" in result.stderr

    project = tmp_path / "project"
    project.mkdir()
    run_id, run_dir = new_run(tmp_path, project)
    (run_dir / "EVIDENCE").rmdir()
    (run_dir / "EVIDENCE").symlink_to(outside, target_is_directory=True)
    gated = call(tmp_path, "gate", "--run", run_id, cwd=project)
    assert gated.returncode == 1
    assert "evidence directory escapes" in gated.stderr


def test_route_records_conditional_capacity_and_rejects_tampering(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    project.mkdir()
    init_git(project)
    run_id, run_dir = new_run(tmp_path, project)
    route(tmp_path, run_id, project)
    artifact = json.loads((run_dir / "ROUTE.json").read_text(encoding="utf-8"))
    assert artifact["source_pool"] == "claude"
    assert artifact["pool"] == "codex"
    assert artifact["capacity_status"] == "headroom-unverified"
    artifact["model"] = "unapproved-model"
    (run_dir / "ROUTE.json").write_text(json.dumps(artifact), encoding="utf-8")
    dry = call(
        tmp_path, "codex", "implement", "--run", run_id, "--dry-run", cwd=project
    )
    assert dry.returncode == 1
    assert "current policy" in dry.stderr or "stale" in dry.stderr


def test_codex_dry_run_is_fully_bound_and_does_not_create_dispatch(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    project.mkdir()
    init_git(project)
    run_id, run_dir = new_run(tmp_path, project)
    route(tmp_path, run_id, project)
    wrong_role = call(
        tmp_path, "codex", "bulk", "--run", run_id, "--dry-run", cwd=project
    )
    assert wrong_role.returncode == 1 and "role differs" in wrong_role.stderr
    other = tmp_path / "other"
    other.mkdir()
    init_git(other)
    wrong_project = call(
        tmp_path,
        "codex",
        "implement",
        "--run",
        run_id,
        "--project",
        str(other),
        "--dry-run",
        cwd=project,
    )
    assert wrong_project.returncode == 1 and "project differs" in wrong_project.stderr
    dry = call(
        tmp_path, "codex", "implement", "--run", run_id, "--dry-run", cwd=project
    )
    assert dry.returncode == 0, dry.stderr
    for flag in (
        "--ignore-user-config",
        "--ignore-rules",
        "--strict-config",
        "--ephemeral",
    ):
        assert flag in dry.stdout
    assert "--skip-git-repo-check" not in dry.stdout
    assert (run_dir / "DISPATCH_PREVIEW.json").exists()
    assert not (run_dir / "DISPATCH.json").exists()
    assert not (run_dir / "RESULT.json").exists()


def test_dry_run_enforces_real_git_check_or_explicit_override(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    run_id, _ = new_run(tmp_path, project)
    route(tmp_path, run_id, project)
    rejected = call(
        tmp_path, "codex", "implement", "--run", run_id, "--dry-run", cwd=project
    )
    assert rejected.returncode == 1 and "Git worktree" in rejected.stderr
    allowed = call(
        tmp_path,
        "codex",
        "implement",
        "--run",
        run_id,
        "--dry-run",
        "--allow-non-git",
        cwd=project,
    )
    assert allowed.returncode == 0
    assert "--skip-git-repo-check" in allowed.stdout


def test_gate_pass_fail_inconclusive_and_explicit_project_trust(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    run_id, run_dir = new_run(tmp_path, project)
    project_override(
        project,
        [
            {
                "id": "ok",
                "argv": [sys.executable, "-c", f"print({SECRET!r})"],
                "hard": True,
            }
        ],
    )
    unapproved = call(tmp_path, "gate", "--run", run_id, cwd=project)
    assert unapproved.returncode == 3
    assert (
        json.loads((run_dir / "VERDICT.json").read_text())["status"] == "inconclusive"
    )
    flag_only = call(
        tmp_path, "gate", "--run", run_id, "--allow-project-gates", cwd=project
    )
    assert flag_only.returncode == 3
    no_run = call(
        tmp_path,
        "gate",
        "--project",
        str(project),
        *project_gate_approval(project),
    )
    assert no_run.returncode == 1 and "run-bound" in no_run.stderr
    approved_args = executable_project_gate_approval(project)
    passed = call(tmp_path, "gate", "--run", run_id, *approved_args, cwd=project)
    assert passed.returncode == 0

    project_override(
        project,
        [
            {
                "id": "bad",
                "argv": [sys.executable, "-c", "raise SystemExit(4)"],
                "hard": True,
            }
        ],
    )
    assert (
        call(
            tmp_path,
            "gate",
            "--run",
            run_id,
            *executable_project_gate_approval(project),
            cwd=project,
        ).returncode
        == 1
    )
    project_override(
        project,
        [
            {
                "id": "skip",
                "argv": [sys.executable, "-c", "raise SystemExit(5)"],
                "hard": True,
                "skip_exit_codes": [5],
                "skip_note": "no evidence",
            }
        ],
    )
    assert (
        call(
            tmp_path,
            "gate",
            "--run",
            run_id,
            *executable_project_gate_approval(project),
            cwd=project,
        ).returncode
        == 3
    )


def test_gate_hard_failure_stops_later_steps(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    run_id, _ = new_run(tmp_path, project)
    first = project / "first.py"
    second = project / "second.py"
    marker_one = project / "first.marker"
    marker_two = project / "second.marker"
    first.write_text(
        f"from pathlib import Path\nPath({str(marker_one)!r}).write_text('x')\nraise SystemExit(4)\n",
        encoding="utf-8",
    )
    second.write_text(
        f"from pathlib import Path\nPath({str(marker_two)!r}).write_text('x')\n",
        encoding="utf-8",
    )
    project_override(
        project,
        [
            {"id": "first", "argv": [sys.executable, str(first)], "hard": True},
            {"id": "second", "argv": [sys.executable, str(second)], "hard": True},
        ],
    )
    result = call(
        tmp_path,
        "gate",
        "--run",
        run_id,
        *executable_project_gate_approval(project),
        cwd=project,
    )
    assert result.returncode == 1
    assert marker_one.exists()
    assert not marker_two.exists()


@pytest.mark.skipif(
    not usable_gate_sandbox(),
    reason="Bubblewrap gate sandbox is unavailable",
)
def test_gate_sandbox_scrubs_secrets_and_blocks_outside_writes(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    project.mkdir()
    outside = tmp_path / "outside.marker"
    outside_secret = tmp_path / "outside.secret"
    outside_secret.write_text(SECRET, encoding="utf-8")
    run_id, run_dir = new_run(tmp_path, project)
    script_path = project / "containment.py"
    script_path.write_text(
        "import os\n"
        "from pathlib import Path\n"
        "if os.getenv('SYNC_TEST_TOKEN'):\n"
        "    raise SystemExit(7)\n"
        f"secret = Path({str(outside_secret)!r})\n"
        "try:\n"
        "    secret.read_text()\n"
        "except OSError:\n"
        "    pass\n"
        "else:\n"
        "    raise SystemExit(8)\n"
        f"target = Path({str(outside)!r})\n"
        "try:\n"
        "    target.write_text('escaped')\n"
        "except OSError:\n"
        "    pass\n"
        "raise SystemExit(0)\n",
        encoding="utf-8",
    )
    project_override(
        project,
        [
            {
                "id": "containment",
                "argv": [sys.executable, str(script_path)],
                "hard": True,
            }
        ],
    )
    result = call(
        tmp_path,
        "gate",
        "--run",
        run_id,
        *project_gate_approval(project),
        cwd=project,
        env_extra={"SYNC_TEST_TOKEN": SECRET, "VIRTUAL_ENV": str(tmp_path)},
    )
    assert result.returncode == 0, result.stderr
    assert not outside.exists()
    verdict = json.loads((run_dir / "VERDICT.json").read_text(encoding="utf-8"))
    assert verdict["steps"][0]["execution_mode"] == "bubblewrap"


def test_unusable_bubblewrap_is_inconclusive(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    run_id, run_dir = new_run(tmp_path, project)
    project_override(
        project,
        [
            {
                "id": "never-runs",
                "argv": [sys.executable, "-c", "raise SystemExit(0)"],
                "hard": True,
            }
        ],
    )
    fake_bin = tmp_path / "fake-sandbox-bin"
    fake_bin.mkdir()
    fake_bwrap = fake_bin / "bwrap"
    fake_bwrap.write_text("#!/bin/sh\nexit 125\n", encoding="utf-8")
    fake_bwrap.chmod(0o755)
    result = call(
        tmp_path,
        "gate",
        "--run",
        run_id,
        *project_gate_approval(project),
        cwd=project,
        env_extra={"PATH": str(fake_bin)},
    )
    assert result.returncode == 3, result.stderr
    verdict = json.loads((run_dir / "VERDICT.json").read_text(encoding="utf-8"))
    assert verdict["status"] == "inconclusive"
    assert verdict["steps"][0]["execution_mode"] == "sandbox-unavailable"
    assert verdict["steps"][0]["reason"] == "sandbox unavailable"


def test_virtual_env_mount_is_validated_and_narrow(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = load_harness()
    monkeypatch.setenv("VIRTUAL_ENV", str(tmp_path))
    assert module.validated_virtual_env() is None

    virtual_env = tmp_path / "venv"
    (virtual_env / "bin").mkdir(parents=True)
    (virtual_env / "lib").mkdir()
    (virtual_env / "pyvenv.cfg").write_text("home = /usr/bin\n", encoding="utf-8")
    python = virtual_env / "bin" / "python"
    python.write_text("#!/bin/sh\n", encoding="utf-8")
    python.chmod(0o755)
    (virtual_env / "do-not-mount.txt").write_text(SECRET, encoding="utf-8")
    monkeypatch.setenv("VIRTUAL_ENV", str(virtual_env))
    assert module.validated_virtual_env() == virtual_env.resolve()

    project = tmp_path / "project"
    scratch = tmp_path / "scratch"
    project.mkdir()
    scratch.mkdir()
    env = module.gate_environment()
    command = module.bubblewrap_command(
        "/usr/bin/bwrap", ["/usr/bin/true"], project, scratch, env
    )
    read_only_mounts = {
        (command[index + 1], command[index + 2])
        for index, item in enumerate(command[:-2])
        if item == "--ro-bind"
    }
    assert (str(virtual_env), str(virtual_env)) not in read_only_mounts
    assert (str(virtual_env / "bin"), str(virtual_env / "bin")) in read_only_mounts
    assert (str(virtual_env / "lib"), str(virtual_env / "lib")) in read_only_mounts


@pytest.mark.parametrize(
    "step,error",
    [
        ({"id": "../escape", "argv": ["true"], "hard": True}, "invalid gate step"),
        ({"id": "bad", "argv": "true", "hard": True}, "argv must"),
        ({"id": "bad", "argv": ["echo", "x;id"], "hard": True}, "forbidden shell"),
        ({"id": "bad", "argv": ["true"], "hard": "yes"}, "hard flag"),
        ({"id": "bad", "argv": ["true"], "hard": True, "timeout": 0}, "timeout"),
    ],
)
def test_malformed_project_gate_fails_cleanly(
    tmp_path: Path, step: dict[str, object], error: str
) -> None:
    project = tmp_path / "project"
    project.mkdir()
    run_id, _ = new_run(tmp_path, project)
    project_override(project, [step])
    result = call(
        tmp_path, "gate", "--run", run_id, "--allow-project-gates", cwd=project
    )
    assert result.returncode == 1
    assert error in result.stderr
    assert "Traceback" not in result.stderr


def test_gate_config_symlink_and_malformed_json_fail_cleanly(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    run_id, _ = new_run(tmp_path, project)
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "gates.json").write_text("{}", encoding="utf-8")
    (project / ".sync").symlink_to(outside, target_is_directory=True)
    result = call(
        tmp_path, "gate", "--run", run_id, "--allow-project-gates", cwd=project
    )
    assert result.returncode == 1
    assert "regular file inside" in result.stderr
    (project / ".sync").unlink()
    (project / ".sync").mkdir()
    (project / ".sync" / "gates.json").write_text("{bad", encoding="utf-8")
    malformed = call(
        tmp_path, "gate", "--run", run_id, "--allow-project-gates", cwd=project
    )
    assert malformed.returncode == 1
    assert "invalid JSON" in malformed.stderr and "Traceback" not in malformed.stderr
    (project / ".sync" / "gates.json").unlink()
    (project / ".sync" / "gates.json").mkdir()
    special = call(
        tmp_path, "gate", "--run", run_id, "--allow-project-gates", cwd=project
    )
    assert special.returncode == 1
    assert "regular file inside" in special.stderr


def test_detector_combination_is_hermetic(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "package.json").write_text("{}", encoding="utf-8")
    (project / "pyproject.toml").write_text("[build-system]\n", encoding="utf-8")
    module = load_harness()
    detectors, steps, fingerprint, is_override = module.detect_steps(project)
    assert detectors == ["node", "python"]
    assert len({step["id"] for step in steps}) == len(steps)
    assert fingerprint and not is_override


def test_hook_remains_fail_closed_without_explicit_operator_override(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    project.mkdir()
    payload = json.dumps({"cwd": str(project), "session_id": "session-one"})
    for _ in range(4):
        result = call(tmp_path, "gate", "--hook", cwd=project, input_text=payload)
        assert result.returncode == 2
        assert "INCONCLUSIVE" in result.stdout
    malformed = call(tmp_path, "gate", "--hook", cwd=project, input_text="{bad")
    assert malformed.returncode == 0
    active = call(
        tmp_path,
        "gate",
        "--hook",
        cwd=project,
        input_text=json.dumps({"cwd": str(project), "stop_hook_active": True}),
    )
    assert active.returncode == 0
    override = call(
        tmp_path,
        "gate",
        "--hook",
        cwd=project,
        input_text=payload,
        env_extra={"SYNC_ALLOW_UNVERIFIED_STOP": "1"},
    )
    assert override.returncode == 0
    assert "Explicit operator override" in override.stderr


def test_all_json_schemas_are_draft_2020_12_valid() -> None:
    schemas = sorted((ROOT / "references" / "schemas").glob("*.schema.json"))
    assert schemas
    for path in schemas:
        schema = json.loads(path.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)


def test_real_fake_dispatch_redacts_binds_gates_and_records(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    init_git(project)
    _, fake_env = fake_codex(tmp_path)
    run_id, run_dir = new_run(tmp_path, project)
    route(tmp_path, run_id, project)
    dispatched = call(
        tmp_path,
        "codex",
        "implement",
        "--run",
        run_id,
        cwd=project,
        env_extra=fake_env,
    )
    assert dispatched.returncode == 0, dispatched.stderr
    dispatch = json.loads((run_dir / "DISPATCH.json").read_text(encoding="utf-8"))
    assert dispatch["result_status"] == "valid"
    assert dispatch["config"]["sandbox"] == "workspace-write"
    assert dispatch["config"]["approval_policy"] == "never"
    assert dispatch["config"]["execpolicy_rules"] == "ignored"
    assert not dispatch["dry_run"] and dispatch["duration_seconds"] >= 0
    for artifact in (
        "DISPATCH.json",
        "RESULT.json",
        "CODEX_EVENTS.jsonl",
        "CODEX_STDERR.log",
    ):
        path = run_dir / artifact
        assert stat.S_IMODE(path.stat().st_mode) == 0o600
        assert SECRET not in path.read_text(encoding="utf-8")
    assert not list(run_dir.glob(".codex-result-*.tmp"))

    project_override(
        project,
        [
            {
                "id": "ok",
                "argv": [sys.executable, "-c", f"print({SECRET!r})"],
                "hard": True,
            }
        ],
    )
    gated = call(
        tmp_path,
        "gate",
        "--run",
        run_id,
        *executable_project_gate_approval(project),
        cwd=project,
    )
    assert gated.returncode == 0, gated.stderr
    recorded = call(
        tmp_path,
        "record",
        "--run",
        run_id,
        "--notes",
        "token=" + SECRET,
        cwd=project,
    )
    assert recorded.returncode == 0, recorded.stderr
    outcome = json.loads((run_dir / "OUTCOME.json").read_text(encoding="utf-8"))
    assert outcome["outcome_status"] == "success"
    assert outcome["capacity_status"] == "headroom-unverified"
    assert outcome["wall_clock_s"] == dispatch["duration_seconds"]
    verdict = json.loads((run_dir / "VERDICT.json").read_text(encoding="utf-8"))
    step = verdict["steps"][0]
    evidence = run_dir / verdict["evidence_dir"] / "ok.log"
    assert hashlib.sha256(evidence.read_bytes()).hexdigest() == step["output_sha256"]
    assert SECRET not in evidence.read_text(encoding="utf-8")
    assert step["execution_mode"] in {"bubblewrap", "unsandboxed-explicit"}
    ledger = tmp_path / "sync-home" / "ledger.jsonl"
    assert stat.S_IMODE(ledger.stat().st_mode) == 0o600
    assert SECRET not in ledger.read_text(encoding="utf-8")
    duplicate = call(tmp_path, "record", "--run", run_id, cwd=project)
    assert duplicate.returncode == 1 and "immutable outcome" in duplicate.stderr
    redispatch = call(
        tmp_path,
        "codex",
        "implement",
        "--run",
        run_id,
        cwd=project,
        env_extra={**fake_env, "FAKE_CODEX_MODE": "fail"},
    )
    assert redispatch.returncode == 1
    assert "already contains dispatch artifacts" in redispatch.stderr


def test_invalid_executor_result_is_not_promoted(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    init_git(project)
    _, fake_env = fake_codex(tmp_path)
    run_id, run_dir = new_run(tmp_path, project)
    route(tmp_path, run_id, project)
    result = call(
        tmp_path,
        "codex",
        "implement",
        "--run",
        run_id,
        cwd=project,
        env_extra={**fake_env, "FAKE_CODEX_MODE": "invalid"},
    )
    assert result.returncode == 4
    dispatch = json.loads((run_dir / "DISPATCH.json").read_text(encoding="utf-8"))
    assert dispatch["result_status"] == "invalid"
    assert dispatch["result_sha256"] is None
    assert not (run_dir / "RESULT.json").exists()
    assert not list(run_dir.glob(".codex-result-*.tmp"))


def test_blocked_executor_cannot_be_recorded_as_success(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    init_git(project)
    _, fake_env = fake_codex(tmp_path)
    run_id, run_dir = new_run(tmp_path, project)
    route(tmp_path, run_id, project)
    dispatched = call(
        tmp_path,
        "codex",
        "implement",
        "--run",
        run_id,
        cwd=project,
        env_extra={**fake_env, "FAKE_CODEX_MODE": "blocked"},
    )
    assert dispatched.returncode == 0, dispatched.stderr
    project_override(
        project,
        [
            {
                "id": "ok",
                "argv": [sys.executable, "-c", "raise SystemExit(0)"],
                "hard": True,
            }
        ],
    )
    gated = call(
        tmp_path,
        "gate",
        "--run",
        run_id,
        *executable_project_gate_approval(project),
        cwd=project,
    )
    assert gated.returncode == 0, gated.stderr
    recorded = call(tmp_path, "record", "--run", run_id, cwd=project)
    assert recorded.returncode == 0, recorded.stderr
    outcome = json.loads((run_dir / "OUTCOME.json").read_text(encoding="utf-8"))
    assert outcome["executor_status"] == "blocked"
    assert outcome["result_validation"] == "valid"
    assert outcome["outcome_status"] == "inconclusive"


def test_tampered_dispatch_and_pre_dispatch_verdict_are_rejected(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    project.mkdir()
    init_git(project)
    _, fake_env = fake_codex(tmp_path)
    run_id, run_dir = new_run(tmp_path, project)
    route(tmp_path, run_id, project)
    project_override(
        project,
        [
            {
                "id": "ok",
                "argv": [sys.executable, "-c", "raise SystemExit(0)"],
                "hard": True,
            }
        ],
    )
    assert (
        call(
            tmp_path,
            "gate",
            "--run",
            run_id,
            *executable_project_gate_approval(project),
            cwd=project,
        ).returncode
        == 0
    )
    assert (
        call(
            tmp_path,
            "codex",
            "implement",
            "--run",
            run_id,
            cwd=project,
            env_extra=fake_env,
        ).returncode
        == 0
    )
    stale = call(tmp_path, "record", "--run", run_id, cwd=project)
    assert stale.returncode == 1 and "not bound" in stale.stderr

    dispatch_path = run_dir / "DISPATCH.json"
    dispatch = json.loads(dispatch_path.read_text(encoding="utf-8"))
    dispatch["config"]["model"] = "tampered"
    dispatch_path.write_text(json.dumps(dispatch), encoding="utf-8")
    tampered = call(
        tmp_path,
        "gate",
        "--run",
        run_id,
        *project_gate_approval(project),
        cwd=project,
    )
    assert tampered.returncode == 1
    assert "configuration fingerprint" in tampered.stderr


def test_command_surfaces_remain_available(tmp_path: Path) -> None:
    for command in ("policy", "measure", "evolve", "doctor"):
        result = call(tmp_path, command)
        if command == "doctor":
            assert result.returncode in {0, 1}
        else:
            assert result.returncode == 0, result.stderr
