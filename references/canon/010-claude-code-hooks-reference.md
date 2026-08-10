---
type: "canon"
title: "010. Claude Code hooks reference"
domain: "Claude and Codex council orchestration: task routing across billing pools, artifact-mediated coordination, ground-truth verification gates, quota and cost measurement, and policy evolution from recorded outcomes"
status: "active"
created: "2026-01-01"
updated: "2026-01-01"
tags:
  - "#domain/claude-and-codex-council-orchestration-task-routing-across-billi"
  - "#type/canon"
  - "#confidence/evidence-based"
confidence: "evidence-based"
related:
  - "[[Claude Code hooks reference 010]]"
  - "[[Index]]"
  - "[[Dashboard]]"
  - "[[CONVENTIONS]]"
  - "[[Tag Taxonomy]]"
  - "[[Source Intake Workflow]]"
  - "[[Research Refresh Workflow]]"
  - "[[Claim Verification Flow]]"
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

# 010. Claude Code hooks reference

Ledger: 010 | source: Claude Code hooks reference | confidence: evidence-based | fold: [[Claude Code hooks reference 010]] | status: captured.

## What It Says

- Hooks are deterministic and guarantee the action happens, unlike advisory instructions
- Exit code 2 blocks the action and the hook's stderr is fed back to Claude
- Any other nonzero exit code does not block

## Source

Source: [Claude Code hooks reference](https://code.claude.com/docs/en/hooks); type official; retrieved 2026-07-07; refresh_due 2026-09-06.

## Brain Hooks

- Folded concept: [[Claude Code hooks reference 010]]
- Source ledger: `references/source-ledger.json`
- Verification path: [[Claim Verification Flow]]
