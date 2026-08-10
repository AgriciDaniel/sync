---
name: sync
description: >
  Run work through the Sync council: classify a task into a role, bind it to a
  harness, model, effort, and billing pool, execute it through an artifact-mediated
  run directory shared by Claude and Codex, gate it on executed commands, and
  record the outcome so routing policy can evolve from evidence. Use when the user
  says "sync", "run this through sync", "council", "route this", "offload to
  codex", "gate this", or asks which model or harness should do a piece of work.
  Also use when the Claude weekly or 5-hour allowance is under pressure and the
  pool inventory can prove an eligible route to a distinct pool with current
  source and destination headroom.
argument-hint: "route | plan | council | gate | measure | evolve | doctor"
license: Proprietary
---

# Sync

Sync exists because routing written as prose degrades silently. The harness
system prompt outranks a paragraph. So the decisions live in
`references/routing-policy.json`, and `bin/sync` enforces them.

**Your job in this skill is classification and synthesis. The script's job is
enforcement and evidence. Do not do each other's work.**

Brain root: the directory containing this skill's parent, referred to below as
`$SYNC`. Runtime state lives in `$SYNC_HOME` (default `~/.sync`).

## The one idea

Route for capacity only when `references/pool-inventory.json` has distinct local
pool declarations, observed non-secret authentication modes, and current
headroom marked available for both source and destination. Product and model
labels are not pool identities. Exact account and workspace identifiers are not
stored. Claude documents shared Claude surfaces; OpenAI documents a shared
agentic pool across Codex, ChatGPT Work, ChatGPT for Excel, and Workspace Agents
where available. Otherwise a route is a preference or cost choice, not a
capacity claim.

## Roles

Never name a model in your reasoning. Name a role and let the table resolve it.

| Role | For | Pool |
|---|---|---|
| `spec` | turning an ambiguous request into an unambiguous brief | claude |
| `orchestrate` | holding requirements and integrating results | claude |
| `implement` | executing a well-specified change | **codex** |
| `bulk` | test triage, lint passes, log reading, renames, docstrings | **codex** |
| `review` | adversarial verification of a diff by a non-author | claude |
| `stuck` | reached only after a trigger fires, never a default | claude |

Preview one with `sync route --role <role>`. Add `--run <id>` to bind and persist
the lane as `ROUTE.json`.

## Escalation is an observation, not an argument

Six triggers are recorded. For `implement` and `bulk`, any fired trigger resolves
the role to `stuck`. Other requested roles retain their role while recording the
trigger. Check them **before** starting, because a trigger evaluated mid-task is
evaluated under sunk cost.

```bash
sync route --files 7 --retries 2 --ambiguous
```

`sync route --role implement --files 9` overrides the role to `stuck` on its own.
That override is enforcement, not advice. Do not argue with it.

The four triggers a script cannot see are yours to judge honestly: root-causing
across components, horizon beyond about an hour of skilled human work, ambiguous
requirements, and concurrency or subtle shared state.

## The loop

### 1. Open a run

```bash
sync run new <slug>
```

Creates `$SYNC_HOME/runs/<id>/` with `BRIEF.md`, `WORK_LOG.md`, `EVIDENCE/`.
The run directory **is** the coordination channel. Members read and write files;
they do not share context. This is what stops a council costing more than solo
work.

### 2. Write the brief at the `spec` role

This is the highest-leverage thing you will do. A brief is cheap, cacheable, and
lifts everything downstream. Fill every section of `BRIEF.md`, and be strict
about two of them:

- **Done criteria** must be commands with exit codes, never adjectives. "Tests
  pass" is not a criterion; `pytest -q` exiting 0 is.
- **Out of scope** prevents helpful unwanted work, which is the most common way a
  delegated run wastes a pool.

If you cannot write an unambiguous brief, that is trigger 4. Escalate rather than
handing ambiguity to a cheaper lane.

### 3. Dispatch execution to an eligible declared route

```bash
sync codex implement --run <id>
```

This consumes the run's stored `ROUTE.json`, then records dispatch provenance in
`DISPATCH.json`, a redacted captured event stream in `CODEX_EVENTS.jsonl`, and the
structured executor artifact in `RESULT.json`. Capacity status is `eligible`
only when both distinct, observed pool declarations have current headroom marked
available. Add `--dry-run` to inspect the dispatch without spending anything.
The bound project must be a Git worktree by default. `--allow-non-git` is an
explicit exception recorded in dispatch provenance.

**What comes back is a claim, not a verdict.** Codex reporting success means
nothing until the gate agrees.

### 4. Gate on ground truth

```bash
sync gate --run <id>
```

Runs the ladder for every detected project type, writes `VERDICT.json`, and saves
captured redacted output to `EVIDENCE/`. On supported Linux systems each command
runs in a network-isolated Bubblewrap sandbox with a private home and a narrow
read-only system and toolchain allowlist. Only the bound project and a private
temporary directory map back as writable host paths, and `.git` is remounted
read-only. Hard failures stop the ladder; there is no value in running the suite
while the type check is red.

A project-owned `.sync/gates.json` is discovered but not trusted by its own
`operator_reviewed` marker. Execution requires a run-bound project, the explicit
`--allow-project-gates` flag, and the exact raw-file SHA-256 through
`--project-gate-sha256`. Any file change invalidates the acknowledgment. The hash
is a stale-config and time-of-check control, not proof of human identity. Owner
authorization remains a caller-policy boundary, so executors and project
instructions must not supply either override without explicit approval. If
Bubblewrap is missing or unusable, the gate is inconclusive unless the operator
explicitly passes `--allow-unsandboxed-gates`.

Three results, and the third is the one people get wrong:

- `pass` executed evidence supports the done criteria
- `fail` executed evidence contradicts the done criteria
- `inconclusive` the runner is absent, found nothing to run, or the available
  evidence cannot settle the result

An inconclusive result is **not** a pass. When you report, name what was not run
or could not settle the outcome and why. A
project with no tests has not been tested, however green the summary looks.

As a Claude Stop hook, a non-pass exits 2 and emits a bounded redacted diagnostic
tail. Missing or invalid hook input and `stop_hook_active` exit 0 to avoid a
self-blocking loop. `SYNC_ALLOW_UNVERIFIED_STOP=1` is a human override that
allows the turn to end without changing the non-pass verdict.

### 5. Review with fresh context

For anything beyond a mechanical change, run the `review` role against the diff
alone. The reviewer must not be the author. A model asked whether its own work
was good is the documented failure mode, not the safeguard: self-repair on own
judgment measured 33.3% against 52.6% with real external feedback.

### 6. Record the outcome

```bash
sync record --run <id>
```

`sync record` derives route, pool, verdict, and timing from run artifacts rather
than trusting CLI self-report. Nothing evolves without this. An unrecorded run is
an anecdote.

## Reporting rules

- Never claim a check you did not run. Name the command and its exit code.
- Distinguish pre-existing failures from ones this work introduced.
- Say what was skipped and what could not be verified.
- A gate result is the only thing that settles whether work is done. Your
  confidence is not evidence, and neither is Codex's.

## The autonomy boundary

Brain maintenance and secretary answers are advisory and read-only. A run-bound
executor may read and make reversible edits inside its canonical project under
the brief. It may run sandboxed gates, choose lanes, escalate, and write run and
ledger artifacts.

It stops at the boundary. **Commit, push, publish, deploy, spend, change accounts
or permissions, or touch anything outside the workspace: ask first.** Capability
is not authorization, and a council without a human signer produces work nobody
owns.

`references/routing-policy.json` holds the full envelope. It is not decoration.

## When NOT to use a council

Reflexive fan-out can add coordination and context cost. Sync does not use an
uncited universal percentage or price claim to decide this. Start with one
session for work that is sequential or tightly coupled, then use a council only
when tracks are independent, a bounded read isolates context, or the declared
pool inventory supports a cross-pool route.

Stay in one session for sequential work, same-file edits, dependency chains, and
anything a single session finishes in a handful of tool calls.

Use the council when tracks are genuinely independent, when a large read would
otherwise flood the main context, or when the inventory makes the route
`eligible`. A distinct label or an assumption that the destination is not
running dry is insufficient.

## Evolution

```bash
sync measure    # pool-labeled runs, outcomes, gate results, and wall clock
sync evolve     # proposals from recorded outcomes, nothing written
sync doctor     # local auth, CLI flags, sandbox, and headroom checks
```

`evolve` refuses to propose anything under ten runs, because a rule changed on
fewer runs is a rule changed on noise.

Treat its output as hypotheses. Apply one at a time and keep measuring, because
the one randomized trial in this area found developers 19% slower with AI tools
while believing they had been sped up 20%. Perception here is not just unreliable,
it inverts. Measure against wall clock and merged work, never against how fast it
felt.
