---
type: "dashboard"
title: "Dashboard"
domain: "Claude and Codex council orchestration: task routing across billing pools, artifact-mediated coordination, ground-truth verification gates, quota and cost measurement, and policy evolution from recorded outcomes"
status: "evergreen"
created: "{{date}}"
updated: "{{date}}"
tags:
  - "#domain/claude-and-codex-council-orchestration-task-routing-across-billi"
  - "#type/dashboard"
  - "#confidence/practitioner"
confidence: "practitioner"
related:
  - "[[Start Here]]"
  - "[[CONVENTIONS]]"
  - "[[Tag Taxonomy]]"
  - "[[Index]]"
  - "[[Overview]]"
  - "[[Hot]]"
  - "[[Log]]"
  - "[[Which products share a billing pool is undocumented by both vendors and must be]]"
  - "[[Does moving execution to the Codex pool measurably extend the Claude week under]]"
  - "[[Paired-run probe same task class solo against council, measured on wall clock, p]]"
  - "[[Dashboard]]"
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
  - "[[wiki/flows/_index|Flows Hub]]"
  - "[[wiki/sources/_index|Sources Hub]]"
  - "[[wiki/concepts/_index|Concepts Hub]]"
  - "[[wiki/decisions/_index|Decisions Hub]]"
  - "[[wiki/deliverables/_index|Deliverables Hub]]"
  - "[[wiki/reports/_index|Reports Hub]]"
  - "[[wiki/questions/_index|Questions Hub]]"
  - "[[wiki/gaps/_index|Gaps Hub]]"
  - "[[wiki/experiments/_index|Experiments Hub]]"
source_urls: []
---

# Dashboard

Dataview views over the vault require the Dataview community plugin. Without Dataview, use the linked seed lists and run `python3 scripts/audit_brain.py --json` for the same gate signals.

## Visual Map

![[brain-relationship-map.svg]]

## Notes by status

```dataview
TABLE status, domain, confidence, updated
FROM "wiki"
WHERE type != "meta"
SORT status ASC, updated DESC
```

## Seeds needing substance

```dataview
LIST
FROM "wiki"
WHERE status = "seed"
SORT file.name ASC
```

## Contested and low-confidence claims

```dataview
LIST
FROM "wiki"
WHERE confidence = "contested" OR contains(tags, "#confidence/contested") OR contains(tags, "#confidence/folklore")
SORT updated DESC
```

## Recently updated

```dataview
TABLE updated, status, confidence
FROM "wiki"
SORT updated DESC
LIMIT 15
```

## Seed Evidence Queue

### Gaps

- [[Which products share a billing pool is undocumented by both vendors and must be]]
- [[No vendor publishes numeric plan limits, so capacity cannot be sized in advance]]
- [[Evidence Coverage Not Yet Verified]]

### Questions

- [[Does moving execution to the Codex pool measurably extend the Claude week under]]
- [[Does the council beat a single session on wall clock and merged work, or only on]]
- [[What Current Official Source Resolves The Highest Risk Claim]]

### Experiments

- [[Paired-run probe same task class solo against council, measured on wall clock, p]]
- [[Pool attribution probe drive one harness to a limit and observe which surfaces d]]
- [[Source To Claim Spot Check Probe]]

Watch for `> [!gap]`, `> [!question]`, `> [!contradiction]`, `> [!stale]`, and `> [!done]` callouts in seed notes.

## Operating Links

- [[Source Intake Workflow]]
- [[Research Refresh Workflow]]
- [[Claim Verification Flow]]
- [[Explore Plan Code Commit]]
- [[Multi-Agent Fan-Out Research Flow]]
- [[Context Compaction Routine]]
- [[Synthesis Workflow]]
- [[Reporting Workflow]]
- [[Approval Queue]]
- [[Health Scorecard]]
- [[Action Roadmap]]
