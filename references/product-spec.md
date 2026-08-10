# Sync Product Spec

## Buyer

An operator running both Claude Code and Codex who wants routing, verification, and capacity decisions enforced by the harness rather than described in prose.

## Domain

Claude and Codex council orchestration: task routing across billing pools, artifact-mediated coordination, ground-truth verification gates, quota and cost measurement, and policy evolution from recorded outcomes

## Core Workflows

- Route: classify a task and bind it to a harness, model, effort, and billing pool before work starts
- Spec: spend the frontier tier on an unambiguous brief, not on the typing
- Council: run Claude and Codex against one artifact-mediated run directory
- Gate: execute the ground-truth check ladder in a bounded sandbox and record captured redacted evidence
- Measure: aggregate valid artifact-derived run counts, wall-clock time, executor outcomes, and gate outcomes
- Evolve: revise routing policy from the outcome ledger, never from impression

## Deliverables

- Routing policy table: role to harness, model, effort, and billing pool
- Escalation trigger card: the observed cliff edges that force the frontier tier
- Verification gate specification: the ordered ground-truth ladder per work class
- Council run report: brief, plan, evidence, verdict, and outcome
- Outcome ledger: artifact-derived pool labels, run time, executor status, gate status, and outcome status; live Claude pressure remains statusline-only
- Enforcement audit: what the doctrine prescribes against what the harness actually executes

## Promise

Turn raw sources and recurring decisions into a persistent, source-cited
operating brain.

## Non-Promises

- No capacity-relief claim unless source and destination have distinct declared pool IDs, observed non-secret authentication modes, and current headroom recorded as available
- No price, quota, or benchmark number without a dated source and the plan or harness it applies to
- No gate result reported from model judgment; a verdict requires a command, an exit code, and captured output
- No commit, push, publish, deploy, spend, account change, or production change without explicit owner approval
- No intentional credential persistence; best-effort redaction and sandbox controls do not prove arbitrary output is secret-free
- No claim of measured improvement without naming the baseline and the measurement
