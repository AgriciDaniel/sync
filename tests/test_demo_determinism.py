from __future__ import annotations

import importlib.util
import json
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
BUILDER_PATH = REPO / "scripts" / "build_demo_vault.py"


def load_builder():
    spec = importlib.util.spec_from_file_location("build_demo_vault", BUILDER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_fixed_input_clean_builds_have_identical_tree_and_bytes() -> None:
    builder = load_builder()

    proof = builder.compare_clean_builds(fixed_date="2026-01-01")

    assert proof["fixed_date"] == "2026-01-01"
    assert proof["directories"] > 0
    assert proof["files"] > 0
    assert len(proof["tree_sha256"]) == 64


def test_build_uses_the_fixed_clock_for_generated_content(tmp_path: Path) -> None:
    builder = load_builder()

    vault = builder.build_demo(tmp_path, fixed_date="2025-02-03")

    manifest = json.loads(
        (vault / ".raw" / ".manifest.json").read_text(encoding="utf-8")
    )
    assert manifest["scaffold_history"][0]["created"] == "2025-02-03"
    assert manifest["sources"][0]["retrieved"] == "2025-02-03"
    assert 'created: "2025-02-03"' in (
        vault / "wiki" / "deliverables" / "Health Scorecard.md"
    ).read_text(encoding="utf-8")
