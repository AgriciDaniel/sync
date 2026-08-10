# Source Map

## Raw Sources

- Claude Code statusline JSON, OpenTelemetry metrics, and session transcripts supplied by the operator
- Codex config.toml, rate-limit surfaces, and session exports supplied by the operator
- Sync run directories, verdict files, and the outcome ledger produced locally

## Enrichment Sources

- Official Anthropic and OpenAI platform, pricing, plan, and harness documentation
- Peer-reviewed and preprint studies on agent routing, self-repair, and multi-agent cost
- Benchmark leaderboards that publish per-instance cost and hold the harness fixed

## Import Strategy

- Copy raw source files into `.raw/sources/`.
- Record path, hash, retrieval date, owner, and source type.
- Record external research sources in `references/source-ledger.json`.
- Record implemented schemas and adapters in `references/adapter-manifest.json`.
- Create a source note under `wiki/sources/`.
- Link affected entities, workflows, and deliverables.
