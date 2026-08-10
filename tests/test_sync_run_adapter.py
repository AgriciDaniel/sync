from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator  # type: ignore[import-untyped]

from sync_brain.adapters.sync_run import AdapterError, import_run, load_run


REPO = Path(__file__).resolve().parent.parent
FIXTURE = REPO / "tests" / "fixtures" / "sync-run" / "20260810120000000000-adapter-pass"


def copy_fixture(tmp_path: Path) -> Path:
    target = tmp_path / FIXTURE.name
    shutil.copytree(FIXTURE, target)
    return target


def test_loads_bound_run_and_matches_public_schema() -> None:
    record = load_run(FIXTURE)
    schema = json.loads(
        (REPO / "references" / "schemas" / "sync-run-adapter.schema.json").read_text(
            encoding="utf-8"
        )
    )
    Draft202012Validator(schema).validate(record)
    assert record["outcome"]["status"] == "success"
    assert record["gate"]["status"] == "pass"
    assert record["project"] == {
        "name": "acme",
        "path_sha256": "2375b48b5ab644e143649523e549369bc32e3dfdd1693dce6a85dad92a55b733",  # pragma: allowlist secret
    }
    serialized = json.dumps(record)
    assert "/workspace/acme" not in serialized
    assert "1 passed" not in serialized
    assert "Fixture implementation completed" not in serialized


def test_rejects_tampered_binding_and_malformed_input(tmp_path: Path) -> None:
    run_dir = copy_fixture(tmp_path)
    outcome_path = run_dir / "OUTCOME.json"
    outcome = json.loads(outcome_path.read_text(encoding="utf-8"))
    outcome["pool"] = "tampered"
    outcome_path.write_text(json.dumps(outcome), encoding="utf-8")
    with pytest.raises(AdapterError, match="outcome pool"):
        load_run(run_dir)

    shutil.rmtree(run_dir)
    run_dir = copy_fixture(tmp_path)
    (run_dir / "ROUTE.json").write_text("{not-json", encoding="utf-8")
    with pytest.raises(AdapterError, match="invalid JSON"):
        load_run(run_dir)


def test_import_needs_no_credentials_and_excludes_arbitrary_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    for name in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "CODEX_API_KEY"):
        monkeypatch.delenv(name, raising=False)
    run_dir = copy_fixture(tmp_path)
    verdict_path = run_dir / "VERDICT.json"
    verdict = json.loads(verdict_path.read_text(encoding="utf-8"))
    secret = "sk" + "-ant-" + "this-must-never-be-imported"  # pragma: allowlist secret
    verdict["steps"][0]["output_tail"] = secret
    verdict_path.write_text(json.dumps(verdict), encoding="utf-8")

    vault = tmp_path / "vault"
    (vault / "wiki" / "reports").mkdir(parents=True)
    (vault / "CODEX.md").write_text("# Test vault\n", encoding="utf-8")
    raw_path, report_path = import_run(vault, run_dir)

    assert raw_path.is_file()
    assert report_path.is_file()
    assert raw_path.stat().st_mode & 0o077 == 0
    combined = raw_path.read_text(encoding="utf-8") + report_path.read_text(
        encoding="utf-8"
    )
    assert secret not in combined
    assert "OUTCOME.json" in combined
    assert ".raw/sync-runs/" in combined


def test_normalized_raw_record_is_immutable(tmp_path: Path) -> None:
    run_dir = copy_fixture(tmp_path)
    vault = tmp_path / "vault"
    (vault / "wiki" / "reports").mkdir(parents=True)
    (vault / "CODEX.md").write_text("# Test vault\n", encoding="utf-8")
    raw_path, _ = import_run(vault, run_dir)
    raw_path.write_text("different\n", encoding="utf-8")
    with pytest.raises(AdapterError, match="immutable normalized run"):
        import_run(vault, run_dir)
