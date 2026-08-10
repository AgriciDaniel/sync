# Sync Operator Kit

## Five-Minute Path

```bash
python -m pip install -e .
sync-brain demo
sync-brain lint --vault examples/sample-vault
sync-brain report --vault examples/sample-vault --html-only
```

Open `examples/sample-vault/` in Obsidian and read:

1. `CODEX.md`
2. `wiki/hot.md`
3. `wiki/index.md`
4. `wiki/meta/dashboard.md`

## Client Vault

```bash
sync-brain new acme --client-name "Acme Co" --owner "Daniel Agrici" --out-dir ~/sync-brain-vaults
sync-brain ingest --vault ~/sync-brain-vaults/acme --file tests/fixtures/sample-source.md
sync-brain synthesize --vault ~/sync-brain-vaults/acme
sync-brain report --vault ~/sync-brain-vaults/acme --html-only
```

## Import A Recorded Sync Run

```bash
sync-brain import-run \
  --vault ~/sync-brain-vaults/acme \
  --run-dir ~/.sync/runs/<run-id>
```

The adapter verifies route, dispatch, result when present, verdict, and outcome
bindings. It stores a sanitized normalized record under `.raw/sync-runs/` and
renders a report that cites the source artifact hashes. It intentionally omits
raw project paths, result prose, captured output tails, and credentials.

## Research Rule

Refresh current official or primary sources before turning this scaffold into a
domain-specific release. If the sources are not refreshed, keep the product in
generic scaffold status.

Research evidence must be written into `references/source-ledger.json` with
source URL, source type, retrieved date, refresh due date, confidence, and claim
coverage. Markdown research notes alone do not satisfy market-ready release.

## Adapter Rule

Domain-adapted status requires `references/adapter-manifest.json` to name real
schemas, importer paths, synthesis modules, report renderers, fixtures, and
tests. Sync currently supports fingerprint-bound Sync run directories. Claude
statusline, telemetry, transcript, Codex configuration, and session export
formats remain planned rather than supported.
