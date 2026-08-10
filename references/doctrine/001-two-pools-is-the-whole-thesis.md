---
type: "doctrine"
title: "001. Two Pools Is the Whole Thesis"
created: "2026-08-09"
updated: "2026-08-10"
status: "developing"
confidence: "practitioner"
---

# 001. Two Pools Is the Whole Thesis

Sync exists only when the operator has two distinct declared local pool IDs,
observed non-secret authentication modes, and current headroom in both. Two
subscriptions, models, or product names do not establish that condition by
themselves. Exact account and workspace identifiers are intentionally not stored.

## The distinction that decides everything

## Documented surface boundaries, refreshed 2026-08-10

Anthropic documents that usage across claude.ai, Claude Code, and Claude Desktop
counts toward the same usage limit. It also documents that usage varies by plan,
conversation complexity, features, model, and effort. The current Max-plan page
describes session limits and a weekly limit across all models, while allowing
other model and feature caps. These statements do not support a universal
Opus-only weekly meter. <https://support.claude.com/en/articles/11647753-how-do-usage-and-length-limits-work>
<https://support.claude.com/en/articles/11049741-what-is-the-max-plan>

OpenAI documents that Codex is included in ChatGPT plans and, where features are
available, shares an agentic usage and credit pool with ChatGPT Work, ChatGPT for
Excel, and Workspace Agents. Codex is therefore not a standalone isolated pool.
<https://help.openai.com/en/articles/11369540-codex-and-chatgpt-plan-usage-limits>
<https://developers.openai.com/codex/pricing>

## Count the meters, then route to the one with headroom

| Documented surface or declared pool | What the documentation establishes | Capacity claim Sync may make |
|---|---|---|---|
| Claude subscription surfaces | claude.ai, Claude Code, and Claude Desktop share the applicable usage limit | A Claude model or surface switch is not a documented pool crossing. |
| OpenAI agentic surfaces | Codex, Work, Excel, and Workspace Agents share the applicable agentic pool | A Codex route may consume the same OpenAI pool as other agentic work. |
| Cross-vendor route | Official pages describe product-surface sharing, not this operator's local authentication state or headroom | Relief is conditional on distinct declared pool IDs, observed non-secret authentication modes, and current headroom in `pool-inventory.json`. |

The inventory uses non-secret local labels, observation dates, and source IDs.
It does not contain credentials or exact account or workspace identifiers. The
current first-party Claude and ChatGPT authentication modes and local declarations
are observed. Current headroom is not, so Sync must describe a particular route
as a preference, quality decision, or cost decision until headroom is recorded.

## What this changes

Use the role table to choose a model and effort for task quality. Treat that as
within-pool demand management. It may reduce consumption, but without a
plan-specific measurement it does not establish a separate meter or a numeric
saving.

## What is still not settled

The exact draw rate per model and the operator's plan-specific headroom remain
unobserved. Exact account or workspace identifiers are deliberately not stored;
the inventory records only observed non-secret authentication modes and local
pool declarations. The historical Anthropic help page that used separate reset
labels is retained in the ledger as a conflicting source, not as a universal
routing rule.

## Consequence for Sync

`implement` and `bulk` may route to the OpenAI lane. That route is eligible for a
capacity claim only when the inventory records a distinct local pool ID, observes
both authentication modes, and marks both headroom values available. Codex is not
presumed better or cheaper, and the route does not itself prove a different
meter.

Every routing claim must name the pool it moves work to. A claim that cannot name
a different pool is a cost optimisation, not a capacity one.

## What this does not prove

The official material does not identify this operator's local authentication
state, establish current headroom, or prove a cross-vendor result for a given
run. The privacy-safe inventory must be rechecked after a plan or identity
change.

## Related

- [[002. The Council Is Two Meters, Not Two Opinions]]
- [[003. A Verdict Is a Command, Not a Claim]]
- [[005. Enforcement Beats Prose]]
