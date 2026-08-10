---
type: "concept"
title: "Claude Code hooks reference"
domain: "Claude and Codex council orchestration: task routing across billing pools, artifact-mediated coordination, ground-truth verification gates, quota and cost measurement, and policy evolution from recorded outcomes"
status: "active"
created: "2026-08-09"
updated: "2026-08-09"
tags:
  - "#domain/claude-and-codex-council-orchestration-task-routing-across-billi"
  - "#type/concept"
  - "#confidence/evidence-based"
confidence: "evidence-based"
related:
  - "[[wiki/concepts/_index|Concepts Hub]]"
  - "[[Claim Verification Flow]]"
  - "[[Index]]"
  - "[[Dashboard]]"
  - "[[CONVENTIONS]]"
  - "[[Tag Taxonomy]]"
  - "[[Source Intake Workflow]]"
  - "[[Research Refresh Workflow]]"
  - "[[Synthesis Workflow]]"
  - "[[Reporting Workflow]]"
  - "[[Source Manifest Guide]]"
  - "[[Best Practices Kernel]]"
  - "[[Health Scorecard]]"
  - "[[Action Roadmap]]"
  - "[[Weekly Report]]"
  - "[[Approval Queue]]"
source_urls:
  - "https://code.claude.com/docs/en/hooks"
---

# Claude Code hooks reference

## What It Says

- Hooks are deterministic and guarantee the action happens, unlike advisory instructions
- Exit code 2 blocks the action and the hook's stderr is fed back to Claude
- Any other nonzero exit code does not block

## Source

Source: [Claude Code hooks reference](https://code.claude.com/docs/en/hooks); type official; retrieved 2026-07-07; refresh_due 2026-09-06.



## Canon Backlink

- Canon ledger entry: [references/canon/010-claude-code-hooks-reference.md](../../../../references/canon/010-claude-code-hooks-reference.md)
- Source ledger: `references/source-ledger.json`

## Related

- [[Claim Verification Flow]]
- [[Source Intake Workflow]]
- [[Research Refresh Workflow]]
