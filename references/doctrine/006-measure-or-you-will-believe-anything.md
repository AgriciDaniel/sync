---
type: "doctrine"
title: "006. Measure or You Will Believe Anything"
created: "2026-08-09"
updated: "2026-08-09"
status: "developing"
confidence: "evidence-based"
---

# 006. Measure or You Will Believe Anything

The most uncomfortable finding in this domain, and the reason every rule in Sync
carries a check.

## Evidence

A randomized controlled trial: 16 experienced open-source developers, 246 real
issues in their own repositories, issues averaging about two hours.

- Developers expected AI to speed them up **24%**.
- They were **19% slower**.
- Afterwards they still believed they had been sped up **20%**.

<https://metr.org/blog/2025-07-10-early-2025-ai-experienced-os-dev-study/>

A roughly forty point gap between outcome and perception, among experts, on their
own code. Perception here does not merely fail. It inverts.

## Consequence for Sync

Sync would feel effective whether or not it works. That is precisely why it keeps
an outcome ledger: run, role, pool, wall clock, gate result, escalations,
retries. `sync evolve` reads only that ledger.

`evolve` refuses to propose a policy change under ten recorded runs, because a
rule changed on fewer runs is a rule changed on noise. Methodology warning worth
keeping from the routing literature: "Single-run results LIED in both directions."

## The measurement that counts

Wall clock and merged work. Not tokens saved, not how thorough the run felt, not
how many members participated. A change that cannot be measured cannot be
defended, and by this evidence will feel successful regardless.

## Applies to this system too

Sync is a harness-improvement claim, and nearly every harness-improvement claim in
circulation is self-reported and self-benchmarked by its author. Sync has not yet
been measured against a baseline. Until the ledger has runs in it, its value is a
hypothesis, and it should be described that way.

## What this does not prove

One trial, one population, one tool generation, on mature open-source
repositories the participants already knew well. It establishes that expert
perception of AI speedup is unreliable in that setting. It does not establish
that the tools fail to help, and it does not transfer cleanly to unfamiliar
codebases or to the mechanical work Sync routes to the cheaper pool.

The honest reading is narrow and still damaging: do not trust the feeling. It is
not a reason to stop, it is a reason to keep the ledger.

## Related

- [[002. The Council Is Two Meters, Not Two Opinions]]
- [[004. Escalation Is an Observation]]
- [[007. The Autonomy Boundary]]
