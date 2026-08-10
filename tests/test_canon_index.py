#!/usr/bin/env python3
"""The canon index must match what is on disk, in both directions.

This test exists because of a specific observed failure: a sibling brain's README
advertised twelve doctrine notes by name while the directory held twenty-two
unrelated source stubs and none of the twelve. The index was trusted, the files
were gone, and nothing caught it.

An index that advertises a note which is not present is worse than no index,
because it is believed. So this is a test rather than a convention.

Run: python3 tests/test_canon_index.py
"""

from __future__ import annotations

import json
import re
import sys
from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_loader
from pathlib import Path
from types import ModuleType

REPO = Path(__file__).resolve().parent.parent
# Doctrine lives OUTSIDE references/canon/ on purpose. synthesize_brain.py
# deletes every .md under canon/ and regenerates it from the source ledger, so
# anything authored there is destroyed on the next pipeline run.
CANON = REPO / "references" / "doctrine"
INDEX = CANON / "_index.md"
POLICY = REPO / "references" / "routing-policy.json"
LADDER = REPO / "references" / "gate-ladder.json"
SYNTHESIZE = REPO / "scripts" / "synthesize_brain.py"
SOURCE_CANON = REPO / "references" / "canon"
SOURCE_LEDGER = REPO / "references" / "source-ledger.json"


def collect_failures() -> list[str]:
    failures: list[str] = []

    def check(condition: bool, message: str) -> None:
        if not condition:
            failures.append(message)

    check(INDEX.is_file(), f"missing {INDEX}")
    if not INDEX.is_file():
        return failures

    index_text = INDEX.read_text(encoding="utf-8")

    on_disk = {p.name for p in CANON.glob("*.md") if p.name != "_index.md"}
    linked = set(re.findall(r"\]\((\d{3}-[a-z0-9-]+\.md)\)", index_text))

    for name in sorted(linked - on_disk):
        failures.append(f"index links {name} but it is not on disk")
    for name in sorted(on_disk - linked):
        failures.append(f"{name} is on disk but not linked from the index")

    # No seed placeholders left behind by the scaffold.
    for name in sorted(on_disk):
        if "method-canon" in name:
            failures.append(f"{name} is an unreplaced scaffold placeholder")

    # Regression guard. The generator deletes and rewrites references/canon/.
    # If doctrine is ever moved back under a directory the generator owns, the
    # next pipeline run destroys it silently. This caught it once already.
    if SYNTHESIZE.is_file():
        src = SYNTHESIZE.read_text(encoding="utf-8")
        generator_owned = re.findall(r'REPO\s*/\s*"references"\s*/\s*"([a-z_]+)"', src)
        for owned in set(generator_owned):
            check(
                CANON.name != owned,
                f"doctrine lives in references/{owned}/, which "
                f"synthesize_brain.py deletes and regenerates. Move it.",
            )

    # Every canon note needs frontmatter and a stated limit. A note that only
    # says what its evidence proves is half a note.
    for name in sorted(on_disk):
        text = (CANON / name).read_text(encoding="utf-8")
        check(text.startswith("---"), f"{name} has no YAML frontmatter")
        check("confidence:" in text, f"{name} declares no confidence tag")
        has_limit = any(
            marker in text
            for marker in (
                "does not prove",
                "Honest status",
                "limit of this rule",
                "What this does not",
                "honestly means",
            )
        )
        check(has_limit, f"{name} never states what its evidence does not prove")

    # The index claims each note is enforced by something. Spot-check that the
    # two machine-readable controls it names actually parse.
    for path in (POLICY, LADDER):
        check(path.is_file(), f"missing {path.name}")
        if path.is_file():
            try:
                json.loads(path.read_text(encoding="utf-8"))
            except ValueError as exc:
                failures.append(f"{path.name} is not valid JSON: {exc}")

    # Every role in the policy must name a pool that the policy defines.
    if POLICY.is_file():
        try:
            policy = json.loads(POLICY.read_text(encoding="utf-8"))
            pools = set(policy.get("pools", {}))
            for role, cfg in policy.get("roles", {}).items():
                check(
                    cfg.get("pool") in pools,
                    f"role '{role}' names undefined pool '{cfg.get('pool')}'",
                )
                check(bool(cfg.get("rationale")), f"role '{role}' has no rationale")
        except ValueError:
            pass

    return failures


def test_canon_index() -> None:
    failures = collect_failures()
    assert not failures, "\n".join(f"- {failure}" for failure in failures)


def load_synthesizer() -> ModuleType:
    loader = SourceFileLoader("sync_synthesize_for_test", str(SYNTHESIZE))
    spec = spec_from_loader(loader.name, loader)
    assert spec and spec.loader
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def collect_generated_canon_failures() -> list[str]:
    """Keep the checked-in generated canon aligned with captured ledger sources."""
    failures: list[str] = []
    if not SYNTHESIZE.is_file():
        return [f"missing generator: {SYNTHESIZE}"]
    if not SOURCE_LEDGER.is_file():
        return [f"missing source ledger: {SOURCE_LEDGER}"]
    try:
        ledger = json.loads(SOURCE_LEDGER.read_text(encoding="utf-8"))
    except ValueError as exc:
        return [f"source ledger is not valid JSON: {exc}"]

    sources = ledger.get("sources") if isinstance(ledger, dict) else None
    if not isinstance(sources, list):
        return ["source ledger has no sources list"]

    synthesizer = load_synthesizer()
    expected: dict[str, dict[str, object]] = {}
    for index, source in enumerate(
        (item for item in sources if synthesizer.is_real_captured_source(item)), start=1
    ):
        title = synthesizer.safe_note_name(
            str(source.get("title", "")).strip(), f"Source {index:03d}"
        )
        filename = (
            f"{index:03d}-{synthesizer.safe_slug(title, f'source-{index:03d}')}.md"
        )
        expected[filename] = source

    actual = {
        path.name for path in SOURCE_CANON.glob("*.md") if path.name != "_index.md"
    }
    if len(actual) != len(expected):
        failures.append(
            f"generated canon count is {len(actual)}, expected {len(expected)} from real captured ledger sources"
        )
    for filename in sorted(set(expected) - actual):
        failures.append(f"ledger source is missing generated canon note: {filename}")
    for filename in sorted(actual - set(expected)):
        failures.append(
            f"generated canon note has no matching real captured ledger source: {filename}"
        )

    for filename, source in expected.items():
        path = SOURCE_CANON / filename
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        url = str(source.get("url", "")).strip()
        if url not in text:
            failures.append(f"{filename} does not contain its ledger URL")
        expected_claims = synthesizer.claim_lines(source)
        if expected_claims not in text:
            failures.append(f"{filename} does not contain its current ledger claims")
    return failures


def test_generated_canon_matches_source_ledger() -> None:
    failures = collect_generated_canon_failures()
    assert not failures, "\n".join(f"- {failure}" for failure in failures)


def main() -> int:
    failures = [*collect_failures(), *collect_generated_canon_failures()]
    if failures:
        print(f"FAIL: {len(failures)} problem(s)")
        for failure in failures:
            print(f"  - {failure}")
        return 1
    print(
        f"ok: canon index matches disk, "
        f"{len(list(CANON.glob('*.md'))) - 1} notes, policy and ladder parse"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
