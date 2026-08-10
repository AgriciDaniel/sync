# Sync Adapter Plan

Status: first real adapter complete on 2026-08-10.

## Raw Input Types

- Claude Code statusline JSON, OpenTelemetry metrics, and session transcripts supplied by the operator
- Codex config.toml, rate-limit surfaces, and session exports supplied by the operator
- Sync run directories, verdict files, and the outcome ledger produced locally

## Implemented Input

- Fingerprint-bound Sync run directories containing `meta.json`, `ROUTE.json`,
  `DISPATCH.json`, `VERDICT.json`, `OUTCOME.json`, and `RESULT.json` when the
  dispatch produced a valid result.
- Importer and synthesis: `sync_brain/adapters/sync_run.py`.
- CLI: `sync-brain import-run`.
- Output schema: `references/schemas/sync-run-adapter.schema.json`.
- Sanitized fixture and executable safety tests are recorded in
  `references/adapter-manifest.json`.

## Planned Inputs

- Claude Code statusline, telemetry, and transcript inputs.
- Codex configuration, rate-limit surfaces, and session exports.

These formats are not supported until each has a schema, importer, sanitized
fixture, report path, malformed-input test, and credential-boundary test.

## Safety Refusals

- No capacity-relief claim unless source and destination have distinct declared pool IDs, observed non-secret authentication modes, and current headroom recorded as available
- No price, quota, or benchmark number without a dated source and the plan or harness it applies to
- No gate result reported from model judgment; a verdict requires a command, an exit code, and captured output
- No commit, push, publish, deploy, spend, account change, or production change without explicit owner approval
- No intentional credential persistence; best-effort redaction and sandbox controls do not prove arbitrary output is secret-free
- No claim of measured improvement without naming the baseline and the measurement

## Completion Gate

The first adapter milestone is complete only while the manifest paths exist and
the audit can execute the fingerprint-bound fixture through the real importer.
