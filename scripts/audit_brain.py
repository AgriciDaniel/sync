#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from datetime import date
from functools import lru_cache
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from sync_brain.adapters.sync_run import AdapterError, load_run  # noqa: E402
from sync_brain.release_verification import validate_evidence  # noqa: E402

RESEARCH_FILES = [
    "references/current-requirements.md",
    "references/market-research.md",
    "references/source-map.md",
    "references/safety-gates.md",
]
SOURCE_PACK_FILES = [
    "references/product-spec.md",
    "references/source-map.md",
    "references/current-requirements.md",
    "references/market-research.md",
    "references/safety-gates.md",
    "references/source-manifest-template.md",
    "references/research-plan.md",
    "references/adapter-plan.md",
    "references/source-ledger.json",
    "references/adapter-manifest.json",
]
PLACEHOLDER_PATTERNS = [
    re.compile(r"\bTBD\b", re.I),
    re.compile(r"research required", re.I),
    re.compile(r"release blocked", re.I),
    re.compile(r"add .* before release", re.I),
    re.compile(r"replace this example", re.I),
]
HIGH_STAKES_TERMS = {
    "accounting",
    "tax",
    "legal",
    "medical",
    "health",
    "finance",
    "financial",
    "compliance",
    "payroll",
    "security",
    "insurance",
    "investment",
}
FAST_MOVING_TERMS = {
    "ads",
    "advertising",
    "api",
    "platform",
    "social",
    "youtube",
    "tiktok",
    "meta",
    "google",
    "linkedin",
    "ai",
}
PRIMARY_SOURCE_TYPES = {
    "official",
    "primary",
    "vendor",
    "regulator",
    "government",
    "standards",
    "standards-body",
    "authority",
    "api-docs",
}
DISALLOWED_SOURCE_HOSTS = {
    "example.com",
    "www.example.com",
    "example.org",
    "www.example.org",
    "example.net",
    "www.example.net",
    "localhost",
    "127.0.0.1",
    "0.0.0.0",
}
MATURITY_SCORE_CAP = {
    "scaffolded": 59,
    "researched": 74,
    "domain-adapted": 84,
    "demo-verified": 89,
    "market-ready": 100,
}
MATURITY_ORDER = [
    "scaffolded",
    "researched",
    "domain-adapted",
    "demo-verified",
    "market-ready",
]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit Sync maturity gates.")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--require", choices=MATURITY_ORDER)
    parser.add_argument("--report-only", action="store_true")
    args = parser.parse_args(argv)

    result = audit_repo()
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"Status: {result['status']}")
        print(f"Score: {result['score']}")
        for failure in result["critical_failures"]:
            print(f"CRITICAL: {failure}")
        for warning in result["warnings"]:
            print(f"WARNING: {warning}")

    if args.require and MATURITY_ORDER.index(result["status"]) < MATURITY_ORDER.index(
        args.require
    ):
        print(
            f"ERROR: required maturity {args.require}, got {result['status']}",
            file=__import__("sys").stderr,
        )
        return 1
    if args.report_only:
        return 0
    return 1 if result["critical_failures"] else 0


def audit_repo() -> dict[str, Any]:
    categories: dict[str, dict[str, Any]] = {}
    critical: list[str] = []
    warnings: list[str] = []

    add_category(categories, "product_clarity", *check_product_clarity())
    add_category(categories, "source_pack", *check_source_pack())
    research_ok, research_score, research_notes, research_critical = check_research()
    add_category(
        categories, "current_research", research_ok, research_score, research_notes
    )
    critical.extend(research_critical)
    adapter_ok, adapter_score, adapter_notes, adapter_critical = check_adapters()
    add_category(
        categories, "domain_adapters", adapter_ok, adapter_score, adapter_notes
    )
    critical.extend(adapter_critical)
    citation_ok, citation_score, citation_notes, citation_critical = check_citations()
    add_category(
        categories, "source_citation", citation_ok, citation_score, citation_notes
    )
    critical.extend(citation_critical)
    add_category(
        categories,
        "sample_vault_structure",
        *check_paths(
            [
                "examples/sample-vault/CODEX.md",
                "examples/sample-vault/.raw/.manifest.json",
                "examples/sample-vault/wiki/hot.md",
                "examples/sample-vault/wiki/reports/Weekly Report.md",
            ]
        ),
    )
    add_category(categories, "demo_determinism", *check_demo_determinism())
    add_category(
        categories, "test_assets_and_ci_wiring", *check_test_assets_and_ci_wiring()
    )
    add_category(categories, "packaging", *check_packaging())
    add_category(
        categories,
        "installability",
        *check_installability(),
    )
    add_category(
        categories,
        "docs",
        *check_paths(
            [
                "README.md",
                "docs/OPERATOR_KIT.md",
                "docs/PRODUCT_BOUNDARIES.md",
                "RELEASE_CHECKLIST.md",
            ]
        ),
    )
    add_category(
        categories,
        "obsidian_vault_quality",
        *check_paths(
            [
                "assets/template-brain/CODEX.md",
                "assets/template-brain/.raw/.manifest.json",
                "assets/template-brain/wiki/hot.md",
                "assets/template-brain/wiki/index.md",
                "assets/template-brain/wiki/overview.md",
                "assets/template-brain/wiki/log.md",
                "assets/template-brain/wiki/meta/dashboard.md",
                "assets/template-brain/wiki/canvases/Onboarding Canvas.canvas",
            ]
        ),
    )
    add_category(categories, "distribution_readiness", *check_distribution_readiness())
    add_category(categories, "release_verification", *check_release_verification())

    for name, category in categories.items():
        if not category["ok"]:
            warnings.append(f"{name}: " + "; ".join(category["notes"][:3]))

    raw_score = round(
        sum(category["score"] for category in categories.values()) / len(categories)
    )
    status = determine_status(categories, raw_score, critical)
    score = min(raw_score, MATURITY_SCORE_CAP[status])
    return {
        "status": status,
        "score": score,
        "market_ready": status == "market-ready",
        "critical_failures": critical,
        "warnings": warnings,
        "categories": categories,
    }


def add_category(
    categories: dict[str, dict[str, Any]],
    name: str,
    ok: bool,
    score: int,
    notes: list[str],
) -> None:
    categories[name] = {"ok": ok, "score": max(0, min(100, score)), "notes": notes}


def check_product_clarity() -> tuple[bool, int, list[str]]:
    text = (read(REPO / "README.md") + "\n" + read(REPO / "SKILL.md")).lower()
    required = ["buyer", "outputs", "boundaries", "quick start", "maturity"]
    notes = [f"missing {term} language" for term in required if term not in text]
    return not notes, 100 - 15 * len(notes), notes


def check_source_pack() -> tuple[bool, int, list[str]]:
    missing = [rel for rel in SOURCE_PACK_FILES if not (REPO / rel).exists()]
    return not missing, 100 - 12 * len(missing), [f"missing {rel}" for rel in missing]


def check_research() -> tuple[bool, int, list[str], list[str]]:
    notes: list[str] = []
    critical: list[str] = []
    score = 100
    context = (
        read(REPO / "references" / "product-spec.md") + "\n" + read(REPO / "README.md")
    )
    requires_fresh = contains_any(context, HIGH_STAKES_TERMS) or contains_any(
        context, FAST_MOVING_TERMS
    )

    for rel in RESEARCH_FILES:
        path = REPO / rel
        if not path.exists():
            notes.append(f"missing {rel}")
            critical.append(f"missing research file: {rel}")
            score -= 25
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if any(pattern.search(text) for pattern in PLACEHOLDER_PATTERNS):
            notes.append(f"placeholder research remains in {rel}")
            critical.append(f"placeholder research remains: {rel}")
            score -= 20
        if rel.endswith("current-requirements.md") and not re.search(
            r"\b20\d\d-\d\d-\d\d\b", text
        ):
            notes.append(f"missing retrieval dates in {rel}")
            score -= 10

    ledger_ok, ledger_score, ledger_notes, ledger_critical = check_source_ledger(
        requires_fresh=requires_fresh
    )
    notes.extend(ledger_notes)
    critical.extend(ledger_critical)
    return not critical and ledger_ok, max(0, min(score, ledger_score)), notes, critical


def check_source_ledger(
    *, requires_fresh: bool
) -> tuple[bool, int, list[str], list[str]]:
    path = REPO / "references" / "source-ledger.json"
    notes: list[str] = []
    critical: list[str] = []
    data, errors = load_json_object(path)
    if errors:
        critical.extend(f"invalid source-ledger.json: {error}" for error in errors)
        return False, 0, notes, critical
    sources = data.get("sources")
    if not isinstance(sources, list) or not sources:
        notes.append("source-ledger.json has no captured sources")
        critical.append("source-ledger has no captured official/primary sources")
        return False, 35, notes, critical

    official_count = 0
    for index, source in enumerate(sources, start=1):
        label = f"source-ledger source #{index}"
        if not isinstance(source, dict):
            critical.append(f"{label} must be an object")
            continue
        source_type = clean_string(source.get("source_type")).lower()
        retrieved = parse_iso_date(clean_string(source.get("retrieved")))
        refresh_due = parse_iso_date(clean_string(source.get("refresh_due")))
        claims = source.get("claims")
        if not clean_string(source.get("title")):
            critical.append(f"{label} missing title")
        if not is_valid_source_url(clean_string(source.get("url"))):
            critical.append(f"{label} has invalid or placeholder URL")
        if source_type in PRIMARY_SOURCE_TYPES:
            official_count += 1
        elif source_type not in {"market", "practitioner", "supporting", "fixture"}:
            critical.append(f"{label} has unsupported source_type")
        if retrieved is None:
            critical.append(f"{label} missing valid retrieved date")
        elif retrieved > date.today():
            critical.append(f"{label} has future retrieved date")
        if not isinstance(claims, list) or not any(
            clean_string(claim) for claim in claims
        ):
            critical.append(f"{label} must list sourced claims")
        if requires_fresh:
            if refresh_due is None:
                critical.append(f"{label} missing valid refresh_due date")
            elif refresh_due < date.today():
                critical.append(f"{label} refresh_due is stale")

    minimum_official = 2 if requires_fresh else 1
    if official_count < minimum_official:
        critical.append(
            f"source-ledger needs at least {minimum_official} official/primary sources"
        )
    return (
        not critical,
        max(0, 100 - 18 * len(critical) - 8 * len(notes)),
        notes,
        critical,
    )


def check_adapters() -> tuple[bool, int, list[str], list[str]]:
    notes: list[str] = []
    critical: list[str] = []
    data, errors = load_json_object(REPO / "references" / "adapter-manifest.json")
    if errors:
        critical.extend(f"invalid adapter-manifest.json: {error}" for error in errors)
        return False, 0, notes, critical
    if data.get("generic_only") is not False:
        notes.append("adapter-manifest declares generic_only=true")
        return False, 55, notes, critical

    required_sections = {
        "input_schemas": "input schema",
        "importers": "importer",
        "synthesis_modules": "synthesis module",
        "report_renderers": "report renderer",
        "fixtures": "fixture",
        "tests": "test",
    }
    for section, label in required_sections.items():
        entries = data.get(section)
        if not isinstance(entries, list) or not entries:
            critical.append(f"adapter-manifest missing {label} entries")
            continue
        for index, entry in enumerate(entries, start=1):
            entry_path = manifest_entry_path(entry)
            if not entry_path:
                critical.append(f"adapter-manifest {section} #{index} missing path")
            elif not (REPO / entry_path).exists():
                critical.append(
                    f"adapter-manifest {section} path does not exist: {entry_path}"
                )
    fixtures = data.get("fixtures")
    if isinstance(fixtures, list) and fixtures:
        fixture_path = manifest_entry_path(fixtures[0])
        try:
            normalized = load_run(REPO / fixture_path)
        except (AdapterError, OSError) as exc:
            critical.append(f"Sync run adapter execution failed: {exc}")
        else:
            if normalized.get("schema_version") != "sync-run-adapter/1":
                critical.append("Sync run adapter returned an unexpected schema")
            else:
                notes.append(
                    "executed the fingerprint-bound Sync run fixture through the real adapter"
                )
    return (
        not critical,
        max(0, 100 - 18 * len(critical) - 8 * len(notes)),
        notes,
        critical,
    )


def check_citations() -> tuple[bool, int, list[str], list[str]]:
    notes: list[str] = []
    critical: list[str] = []
    for folder in [
        "assets/template-brain/wiki/deliverables",
        "assets/template-brain/wiki/reports",
        "examples/sample-vault/wiki/deliverables",
        "examples/sample-vault/wiki/reports",
    ]:
        root = REPO / folder
        if not root.exists():
            continue
        for path in root.rglob("*.md"):
            text = path.read_text(encoding="utf-8", errors="replace")
            if (
                "[[" not in text
                and ".raw/" not in text
                and "sha256" not in text.lower()
            ):
                rel = path.relative_to(REPO).as_posix()
                notes.append(f"missing source citation in {rel}")
                critical.append(f"unsourced deliverable/report: {rel}")
    return not critical, max(0, 100 - 15 * len(critical)), notes, critical


def check_packaging() -> tuple[bool, int, list[str]]:
    path = REPO / "scripts" / "package_release.py"
    if not path.exists():
        return False, 0, ["missing scripts/package_release.py"]
    text = path.read_text(encoding="utf-8", errors="replace")
    notes = [
        f"package script missing {term}"
        for term in [
            "SHA256SUMS",
            "RELEASE_MANIFEST",
            "release-type",
            "market-ready",
            "audit_brain.py",
        ]
        if term not in text
    ]
    evidence_ok, evidence_notes, _ = verification_status()
    if not evidence_ok:
        notes.extend(evidence_notes)
    else:
        notes.append(
            "current source-bound acceptance evidence executed the reproducible release tests"
        )
    return (
        evidence_ok
        and not any(note.startswith("package script missing") for note in notes),
        (100 if evidence_ok else 60),
        notes,
    )


def check_demo_determinism() -> tuple[bool, int, list[str]]:
    """Execute the fixed-input byte and tree comparison in isolated directories."""
    with tempfile.TemporaryDirectory(prefix="sync-audit-demo-") as temporary:
        proc = subprocess.run(
            [
                sys.executable,
                str(REPO / "scripts" / "build_demo_vault.py"),
                "--verify-determinism",
                "--out-dir",
                temporary,
            ],
            cwd=REPO,
            text=True,
            capture_output=True,
            check=False,
        )
    if proc.returncode:
        detail = (proc.stderr or proc.stdout).strip()[-500:]
        return False, 0, [f"fixed-input demo comparison failed: {detail}"]
    proof = next(
        (line for line in proc.stdout.splitlines() if '"tree_sha256"' in line), ""
    )
    return True, 100, [f"executed two clean fixed-input builds: {proof}"]


def check_installability() -> tuple[bool, int, list[str]]:
    paths_ok, _, notes = check_paths(
        ["install.sh", "uninstall.sh", "bin/sync-install", "pyproject.toml"]
    )
    evidence_ok, evidence_notes, _ = verification_status()
    if not evidence_ok:
        notes.extend(evidence_notes)
    else:
        notes.append(
            "current source-bound acceptance evidence executed transactional install and rollback tests"
        )
    return paths_ok and evidence_ok, (100 if paths_ok and evidence_ok else 60), notes


def check_distribution_readiness() -> tuple[bool, int, list[str]]:
    notes: list[str] = []
    license_text = read(REPO / "LICENSE")
    metadata = (
        read(REPO / "pyproject.toml")
        + read(REPO / "SKILL.md")
        + read(REPO / "skills" / "sync" / "SKILL.md")
    )
    if "Replace this file" in license_text or "Custom license" in license_text:
        notes.append("distribution license is still an unresolved placeholder")
    if "Custom license" in metadata:
        notes.append("package and skill metadata still declare a placeholder license")
    if "Add notices" in read(REPO / "THIRD_PARTY_NOTICES.md"):
        notes.append("third-party notices are still a placeholder")
    changelog = read(REPO / "CHANGELOG.md")
    if not re.search(r"##\s+\d+\.\d+\.\d+\s+-\s+20\d\d-\d\d-\d\d", changelog):
        notes.append("changelog has no dated semantic-version release entry")
    return not notes, max(0, 100 - 25 * len(notes)), notes


@lru_cache(maxsize=1)
def verification_status() -> tuple[bool, list[str], dict[str, Any]]:
    return validate_evidence(REPO)


def check_release_verification() -> tuple[bool, int, list[str]]:
    ok, notes, evidence = verification_status()
    if ok:
        checks = evidence.get("checks", [])
        return (
            True,
            100,
            [
                f"current source-bound evidence records {len(checks)} executed acceptance checks"
            ],
        )
    return False, 0, notes


def check_test_assets_and_ci_wiring() -> tuple[bool, int, list[str]]:
    required = [
        "tests/test_pipeline.py",
        "tests/test_canon_index.py",
        "tests/test_sync_harness.py",
        "tests/test_sync_run_adapter.py",
        "tests/test_demo_determinism.py",
        "tests/test_release_reproducibility.py",
        "tests/test_installer_rollback.py",
        ".github/workflows/ci.yml",
    ]
    missing = [rel for rel in required if not (REPO / rel).exists()]
    if missing:
        return False, 100 - 12 * len(missing), [f"missing {rel}" for rel in missing]
    ci_text = read(REPO / ".github/workflows/ci.yml")
    if "python -m pytest" not in ci_text:
        return False, 80, ["CI does not invoke pytest"]
    return (
        True,
        100,
        [
            "test assets and pytest CI wiring are present; this audit does not execute tests or report a runtime pass",
        ],
    )


def check_paths(paths: list[str]) -> tuple[bool, int, list[str]]:
    missing = [rel for rel in paths if not (REPO / rel).exists()]
    return not missing, 100 - 12 * len(missing), [f"missing {rel}" for rel in missing]


def determine_status(
    categories: dict[str, dict[str, Any]], score: int, critical: list[str]
) -> str:
    if not categories["current_research"]["ok"]:
        return "scaffolded"
    if not categories["domain_adapters"]["ok"]:
        return "researched"
    if (
        not categories["demo_determinism"]["ok"]
        or not categories["test_assets_and_ci_wiring"]["ok"]
    ):
        return "domain-adapted"
    if (
        critical
        or score < 90
        or any(
            not categories[name]["ok"]
            for name in [
                "packaging",
                "installability",
                "docs",
                "source_citation",
                "obsidian_vault_quality",
                "distribution_readiness",
                "release_verification",
            ]
        )
    ):
        return "demo-verified"
    return "market-ready"


def load_json_object(path: Path) -> tuple[dict[str, Any], list[str]]:
    if not path.exists():
        return {}, [f"missing {path.relative_to(REPO).as_posix()}"]
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except ValueError as exc:
        return {}, [str(exc)]
    if not isinstance(data, dict):
        return {}, ["top-level value must be an object"]
    return data, []


def contains_any(text: str, terms: set[str]) -> bool:
    lowered = text.lower()
    return any(term in lowered for term in terms)


def clean_string(value: object) -> str:
    return value.strip() if isinstance(value, str) else ""


def parse_iso_date(value: str) -> date | None:
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def is_valid_source_url(value: str) -> bool:
    parsed = urlparse(value)
    host = parsed.netloc.lower()
    return (
        parsed.scheme in {"http", "https"}
        and bool(host)
        and host not in DISALLOWED_SOURCE_HOSTS
        and "TBD" not in value.upper()
    )


def manifest_entry_path(entry: object) -> str:
    if isinstance(entry, str):
        return entry
    if not isinstance(entry, dict):
        return ""
    for key in ["path", "schema_path", "module", "fixture", "test"]:
        value = entry.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except FileNotFoundError:
        return ""


if __name__ == "__main__":
    raise SystemExit(main())
