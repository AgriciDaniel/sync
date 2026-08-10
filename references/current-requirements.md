# Current Requirements

Operating requirements Sync depends on. Every entry carries a retrieval date.
Anything here that moves invalidates a routing decision, so this file is the
first thing to recheck when Sync behaves unexpectedly.

Retrieved 2026-08-09 unless stated otherwise. Refresh due 2026-09-08.

## Pool and usage requirements

| Requirement | Detail | Retrieved | Source |
|---|---|---|---|
| Claude shared surfaces | claude.ai, Claude Code, and Claude Desktop count toward the same usage limit when used on the applicable subscription. | 2026-08-10 | `claude-usage-length-limits` |
| Claude usage variability | Usage depends on conversation length and complexity, features, model, effort, and plan. The Max-plan description documents session and weekly limits across all models, with discretionary model and feature caps. | 2026-08-10 | `claude-usage-length-limits`; `claude-max-plan` |
| Claude Code plan binding | Pro and Max users authenticate Claude Code with the same Claude credentials; activity counts against shared Claude and Claude Code limits. API-key authentication instead incurs API charges. | 2026-08-10 | `claude-code-pro-max-plan`; `claude-usage-length-limits` |
| OpenAI shared agentic pool | Codex, ChatGPT Work, ChatGPT for Excel, and Workspace Agents draw from the same agentic usage and credit pool when available on the plan. | 2026-08-10 | `openai-codex-chatgpt-usage-limits`; `openai-codex-pricing` |
| Capacity claim precondition | A capacity route needs distinct declared local pool IDs, observed non-secret authentication modes, and current source and destination headroom in `references/pool-inventory.json`. Exact account and workspace identifiers are intentionally not stored. Product, model, and vendor names alone do not establish relief. | 2026-08-10 | Sync control, documented-surface inputs above |

Consequence for Sync: do not call Codex a standalone pool. Do not call a Claude
model switch a pool crossing. A route is `eligible` only when the privacy-safe
declarations differ, both auth modes are observed, and both headroom values are
currently available.

## Claude Code harness

| Requirement | Detail | Retrieved | Source |
|---|---|---|---|
| Hook blocking semantics | Exit code 2 blocks the action and stderr is returned to the model. Any other nonzero code does not block. | 2026-07-07 | https://code.claude.com/docs/en/hooks |
| Stop hook loop guard | The payload carries `stop_hook_active`. A gate that ignores it can re-block its own retry. | 2026-08-09 | verified live against `bin/sync gate --hook` |
| Statusline quota fields | `rate_limits.five_hour.used_percentage`, `rate_limits.seven_day.used_percentage`, and `resets_at` epochs for both. | 2026-08-07 | https://code.claude.com/docs/en/statusline |
| Statusline availability | Present only for Pro and Max subscribers, only after the first API response in a session, and each window may be independently absent. | 2026-08-07 | https://code.claude.com/docs/en/statusline |
| Settings merge safety | Hooks are arrays per event. Appending preserves existing entries; assigning replaces them. | 2026-08-09 | verified live by `bin/sync-install` dry run against a populated settings.json |
| Model aliases | Claude Code documents `best` as the most capable available alias, currently equivalent to `opus`; `sonnet` and `opus` track recommended provider versions and can move over time. | 2026-08-10 | `claude-code-model-configuration` |
| Effort | Claude Code documents explicit effort levels as a depth, speed, and usage control. Availability varies by active model. | 2026-08-10 | `claude-code-model-configuration` |

Consequence for Sync: `sync gate --hook` must exit 2 to block, must read
`stop_hook_active` defensively, and must exit 0 when the payload is missing or
unparseable. `SYNC_ALLOW_UNVERIFIED_STOP=1` is an explicit operator override that
allows turn end while preserving the non-pass verdict. A gate that blocks on its
own malformed hook input is worse than no gate.

## Codex harness

| Requirement | Detail | Retrieved | Source |
|---|---|---|---|
| Non-interactive entry point | `codex exec [PROMPT]` runs without a TTY. | 2026-08-09 | `codex exec --help`, codex-cli 0.146.0 |
| Artifact output | `-o, --output-last-message <FILE>` writes the final message to a file. | 2026-08-09 | same |
| Typed output | `--output-schema <FILE>` accepts a JSON Schema for the final response shape. | 2026-08-09 | same |
| Sandbox modes | `read-only`, `workspace-write`, `danger-full-access`. | 2026-08-09 | same |
| Working root | `-C, --cd <DIR>`, plus `--skip-git-repo-check` for non-repo directories. | 2026-08-09 | same |
| Per-call model and effort | `-m <MODEL>` and `-c model_reasoning_effort=<level>`. | 2026-08-09 | same |
| Callable model ids | `gpt-5.6-terra` and `gpt-5.6-luna` both returned exit 0 with no substitution. | 2026-08-09 | called live on this account |
| Current model routing guidance | OpenAI positions GPT-5.6 Sol for frontier capability, Terra for balanced intelligence and cost, and Luna for efficient high-volume work. Medium effort is its balanced starting point. | 2026-08-10 | `openai-model-guidance-gpt-5-6` |

Consequence for Sync: the Codex bridge uses `--output-last-message` so the
council coordinates through a file rather than a transcript, and runs under
`workspace-write` with user configuration and project rules ignored. The final
message must pass the local result schema. A declared `blocked` or
`needs_clarification` result cannot be recorded as success even when project
checks pass.

## Local gate containment

| Requirement | Detail | Retrieved | Source |
|---|---|---|---|
| Gate command isolation | On this Linux host, Bubblewrap can run an argv-only command with network namespaces unshared, a private home, a narrow read-only system and toolchain allowlist, only the canonical project plus a private temporary directory writable on the host, and `.git` remounted read-only. | 2026-08-10 | verified live by `tests/test_sync_harness.py::test_gate_sandbox_scrubs_secrets_and_blocks_outside_writes` |
| Project gate integrity | Execution requires a run-bound project, an explicit flag, and a caller-supplied SHA-256 matching the exact raw gate file. This prevents stale-config execution but does not authenticate a human. | 2026-08-10 | Sync control verified by `tests/test_sync_harness.py` |

Consequence for Sync: a missing supported sandbox is inconclusive, not pass.
Unsandboxed execution and exact project-gate acknowledgment are explicit
operator overrides. Owner authorization remains a caller-policy boundary because
a local hash is not a human credential. Gate subprocess environments omit
unapproved variables and mount only the project, a private temporary directory,
and narrow runtime dependencies. This is defense in depth, not proof that
arbitrary project output contains no sensitive data.

## Observed operating constraint

Codex emitted this warning during a live call on 2026-08-09:

> Exceeded skills context budget of 2%. All skill descriptions were removed and
> 171 additional skills were not included in the model-visible skills list.

Consequence: on this machine Codex cannot see skill descriptions at all. Any Sync
design that assumed Codex would discover a skill by description would fail
silently. The bridge therefore passes the full brief inline in the prompt and
does not rely on skill discovery.

## Unverified and deliberately not claimed

- **This operator's pool identities and headroom.** Official documentation
  describes shared product surfaces, not the account or workspace authenticated
  in a particular local harness. The inventory must be observed after each plan
  or identity change.
- **A universal model-specific Claude meter.** Current official plan material
  documents model- and effort-dependent usage and a weekly limit across models,
  not a universal Opus-only weekly meter.
- **Numeric capacity or cost for this workflow.** Plan availability, credits,
  rates, and task consumption vary by plan and work. Do not derive an invoice or
  capacity forecast from an estimated dollar conversion or another operator's
  report.
