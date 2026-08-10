# Sync Agent Instructions

The canonical agent entrypoint is `SKILL.md`; this file exists for agent
runtimes that load project-level `AGENTS.md` instructions.

## Read Order

1. `SKILL.md`
2. `README.md`
3. `docs/OPERATOR_KIT.md`
4. `docs/PRODUCT_BOUNDARIES.md`
5. `references/product-spec.md`
6. `references/source-ledger.json`
7. `references/adapter-manifest.json`
8. `agents/sync-secretary.md`

## Operating Rules

- Do not call this brain market-ready unless `scripts/audit_brain.py --require
  market-ready` passes.
- A scaffold is not a finished brain.
- Domain-specific claims require dated trustworthy sources.
- Research evidence must be recorded in `references/source-ledger.json`.
- Adapter completion must be recorded in `references/adapter-manifest.json`.
- Preserve `.raw/` as immutable source material.
- Keep Obsidian `wiki/`, `CODEX.md`, dashboards, canvases, frontmatter,
  wikilinks, graph hygiene, and source citations healthy.
- Brain maintenance and secretary answers are advisory and read-only. The
  operating `sync` harness may perform reversible edits only inside a run-bound
  canonical project under a bounded brief. External, irreversible, or
  human-boundary actions still require explicit approval and rollback.
- For grounded answers or vault maintenance, use `agents/sync-secretary.md`.
  It must cite a vault note and an official URL for any domain claim.

## Verification

```bash
python -m compileall scripts sync_brain tests
python tests/test_pipeline.py
python scripts/audit_brain.py --json
python scripts/package_release.py --version 0.1.0
```
