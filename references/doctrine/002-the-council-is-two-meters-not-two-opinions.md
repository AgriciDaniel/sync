---
type: "doctrine"
title: "002. The Council Is Two Meters, Not Two Opinions"
created: "2026-08-09"
updated: "2026-08-10"
status: "developing"
confidence: "contested"
---

# 002. The Council Is Two Meters, Not Two Opinions

Most multi-agent systems rest on the belief that more perspectives produce better
work. The measured evidence does not support that for coding, and Sync does not
rest on it.

## Evidence against reflexive fan-out

The recorded vendor research says agents used roughly four times the tokens of
chat and its multi-agent system roughly fifteen times, in a browse-research
setting. The same source cautions that coding has fewer genuinely parallelizable
tasks. <https://www.anthropic.com/engineering/multi-agent-research-system>

Previously recorded exact community cost, percentage, and benchmark comparisons
are not retained here because this repository lacks dated primary provenance for
them. They must not be used for pricing, demand, or capacity claims.

The largest published multi-agent win, 90.2% over single-agent, was measured on
breadth-first browse research, and the same vendor notes coding has fewer
parallelizable tasks. A 2026 paper argues single-agent matches or beats
multi-agent under equal thinking-token budgets. <https://arxiv.org/abs/2604.02460>

## Why Sync's council survives that evidence

Because its justification is conditional, not epistemic. A cross-harness council
has a capacity rationale only when its work moves between distinct declared local
pool IDs, both non-secret authentication modes are observed, and both source and
destination headroom values are available. Exact account and workspace IDs are
intentionally not stored. A second harness that shares the same declaration or
lacks current headroom does not satisfy that condition.

Three properties keep the measured penalty off:

1. **Artifact-mediated.** Members coordinate through a run directory on disk, not
   through shared context. The double context penalty is a shared-context tax.
2. **Bounded briefs.** Each member gets scope, done criteria, and non-scope. No
   member re-reads the whole background.
3. **Ground-truth gated.** Synthesis waits on a command, not on a member's
   report, so coordination does not expand into re-litigation.

## Where a council still earns its cost on judgment

Adversarial verification, where independent verifiers each try to refute a
finding, and design panels where the solution space is genuinely wide. Diversity
of lens beats redundancy: correctness, security, performance, does-it-reproduce.

## Where it is a money fire

Sequential work, same-file edits, dependency chains, and anything one session
finishes in a handful of tool calls.

## Honest status

Marked contested. The vendor and community evidence genuinely disagree, and they
disagree because they measured different task classes. Sync's pool argument is
testable only after the inventory has distinct local declarations, observes both
authentication modes, and records both headroom values as available. Headroom is
currently unrecorded, so the council remains a workflow choice, not a capacity
theorem.

## Related

- [[001. Two Pools Is the Whole Thesis]]
- [[003. A Verdict Is a Command, Not a Claim]]
- [[004. Escalation Is an Observation]]
