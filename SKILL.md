---
name: sync-brain
description: >
  Maintain the Sync brain: ingest sources, synthesize canon, render reports, lint
  the vault, and audit maturity. Use when the user wants to add evidence to Sync,
  refresh its research, check its audit score, or edit its doctrine.
  For running actual work through the council (routing, briefs, Codex dispatch,
  verification gates, measurement), use the `sync` skill instead, not this one.
argument-hint: "ingest | import-run | synthesize | report | visuals | lint | next | audit"
license: Proprietary
---

# Sync Brain (maintenance surface)

This is the brain-maintenance skill. **If you want to run work through Sync, use
the `sync` skill at `skills/sync/SKILL.md`.** That is the operating layer:
routing, briefs, the Claude and Codex council, gates, and measurement.

This skill covers the layer underneath: keeping the doctrine and its evidence
honest.

Operate the deployed vault first. Treat `CODEX.md`, `wiki/hot.md`, and
`wiki/index.md` as vault-root-relative paths, where the vault root is the
directory passed to `--vault` or opened in Obsidian. In this repo, the template
vault root is `assets/template-brain/` and the demo vault root is
`examples/sample-vault/`.

## Canon rules specific to Sync

- Every canon note states what its evidence **does not** prove. Enforced by
  `tests/test_canon_index.py`.
- The canon index must match disk in both directions. Same test. This exists
  because an index that advertises missing notes is trusted and wrong.
- Every doctrine claim names the control that enforces it, or it is not doctrine,
  it is an opinion with a citation.

Secretary: use `agents/sync-secretary.md` for grounded answers, claim review,
and vault maintenance. That secretary reads the brain first, cites a vault note
and an official URL, and stays advisory and read-only.

## Commands

```bash
/sync-brain new <client-slug> --owner <name>
/sync-brain ingest --vault <path> --file <source>
/sync-brain import-run --vault <path> --run-dir <sync-run-directory>
/sync-brain synthesize --vault <path>
/sync-brain report --vault <path>
/sync-brain visuals --vault <path>
/sync-brain lint --vault <path>
/sync-brain next --vault <path>
```

Source checkout equivalent:

```bash
sync-brain new <client-slug> --owner <name>
sync-brain ingest --vault <path> --file <source>
sync-brain import-run --vault <path> --run-dir <sync-run-directory>
sync-brain synthesize --vault <path>
sync-brain report --vault <path> --html-only
```

## Required Operating Rules

1. Read `<vault>/CODEX.md`.
2. Read `<vault>/wiki/hot.md`.
3. Read `<vault>/wiki/index.md`.
4. Preserve `.raw/` as immutable source material.
5. Never store credentials in the vault.
6. Never make domain-specific claims without dated trustworthy sources.
7. Keep `hot`, `index`, `overview`, and `log` current.
8. Record research evidence in `references/source-ledger.json`.
9. Record domain adapter completion in `references/adapter-manifest.json`.

## Script Mapping

- `new` -> `python scripts/scaffold_vault.py`
- `ingest` -> `python scripts/ingest_source.py`
- `import-run` -> `sync_brain.adapters.sync_run.import_run`
- `synthesize` -> `python scripts/synthesize_brain.py`
- `report` -> `python scripts/render_brain_report.py`
- `visuals` -> `python scripts/generate_vault_visuals.py`
- `lint` -> `python scripts/lint_vault.py`
- `next` -> `python scripts/guide_next_action.py`

## Quality Gates

- No capacity-relief claim unless source and destination have distinct declared pool IDs, observed non-secret authentication modes, and current headroom recorded as available
- No price, quota, or benchmark number without a dated source and the plan or harness it applies to
- No gate result reported from model judgment; a verdict requires a command, an exit code, and captured output
- No commit, push, publish, deploy, spend, account change, or production change without explicit owner approval
- No intentional credential persistence; best-effort redaction and sandbox controls do not prove arbitrary output is secret-free
- No claim of measured improvement without naming the baseline and the measurement

Do not call this brain market-ready unless `scripts/audit_brain.py --require
market-ready` passes. A scaffold is not a finished brain.

## Research Refresh

monthly for prices, quotas, model rosters, and plan limits; before every release for official harness requirements; benchmark leaderboards rechecked each refresh because several are silently frozen
