---
type: "platform"
title: "Importer Sync run directory importer"
domain: "Claude and Codex council orchestration: task routing across billing pools, artifact-mediated coordination, ground-truth verification gates, quota and cost measurement, and policy evolution from recorded outcomes"
status: "active"
created: "2026-01-01"
updated: "2026-01-01"
tags:
  - "#domain/claude-and-codex-council-orchestration-task-routing-across-billi"
  - "#type/platform"
  - "#confidence/practitioner"
confidence: "practitioner"
related:
  - "[[wiki/platforms/_index|Platforms Hub]]"
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
source_urls: []
---

# Importer Sync run directory importer

## Adapter Evidence

This importer note was folded from `references/adapter-manifest.json`, section `importers`.

- name: `Sync run directory importer`
- path: `sync_brain/adapters/sync_run.py`
- entrypoint: `sync-brain import-run`
- credentials: `none`
- safety: `Rejects symlinks, oversized artifacts, malformed JSON, and broken route, dispatch, verdict, result, or outcome bindings`


## Manifest Backlink

- Adapter manifest: `references/adapter-manifest.json`

## Related

- [[Dashboard]]
- [[Synthesis Workflow]]
- [[Reporting Workflow]]
