# Market Research

What already exists in this space, and where Sync differs. Retrieved 2026-08-09.
Refresh due 2026-09-08.

The honest summary: the individual ideas in Sync are not novel. Routing tables,
verification hooks, and multi-agent councils all exist in public tooling. What is
uncommon is the combination of a **cross-pool** justification with a **ground
truth** gate and a **recorded ledger** that is allowed to overturn the policy.

## Adjacent categories

| Category | Examples | What it solves | What it leaves open |
|---|---|---|---|
| Gateway routers | LiteLLM, OpenRouter, claude-code-router | One endpoint, many providers, per-token cost control | Routes by price, not by allowance. Pointing a harness at a non-first-party base URL costs deferred tool loading and complicates prompt caching, so the interactive surface pays for savings on the cheap one |
| Harness hook packs | Community Claude Code hook collections | Deterministic formatting, guards, and gates | Usually per-project and per-harness, and rarely tied to a routing decision |
| Multi-agent frameworks | Orchestrator and worker patterns, agent teams | Parallelism and specialisation | Can add coordination and context cost. This repository has no dated primary evidence for a universal coding-cost percentage. |
| Usage monitors | ccusage, claude-monitor | Spend history and limit warnings | Answer "what did I burn", not "which meter should the next task use" |
| Agent nests | Buzz (`~/.buzz`, Block) | Artifact-mediated coordination, per-agent identity, one skill across four harnesses | A coordination substrate rather than a routing or verification policy |

## Where Sync sits

Sync is not a gateway. It keeps its harness configuration explicit and records
the route and evidence for each run. This repository does not make a numeric
token, price, or performance claim for that choice without current primary
evidence that applies to the configured harness.

Instead of assuming that a provider, product, or model is a separate allowance,
Sync checks a privacy-safe declared pool inventory. Moving work can be called
eligible for capacity relief only when it crosses distinct declared local pool
IDs, both non-secret authentication modes are observed, and both pools have
current headroom recorded as available.

The three-part combination:

1. **Cross-pool routing.** Every role names the meter it draws on. Claims that
   cannot name a different pool are labelled cost optimisations, not capacity ones.
2. **Ground-truth gating.** A verdict is a command and an exit code. The Stop hook
   blocks turn-end at exit 2. Skips are reported as skips.
3. **Ledger-driven policy.** `sync evolve` reads only recorded outcomes and
   refuses to propose anything under ten runs.

## Demand signal

No dated, primary demand evidence is currently recorded for the claimed
two-subscription workflow. Operator reports and plan-price anecdotes are not used
as demand, price, or capacity evidence. The testable proposition is narrower:
given distinct declared pool IDs, observed non-secret authentication modes, and
recorded headroom, Sync can measure whether routing preserves the source pool's
headroom for this operator.

## Honest competitive position

- Sync has **no measured advantage yet**. No validated schema-v2 baseline is
  bundled. Every claim here is about mechanism, not outcome.
- The multi-agent evidence does not establish a universal coding-cost result.
  Sync's cross-pool premise is conditional on privacy-safe pool declarations,
  observed authentication modes, and current headroom. It remains unmeasured for
  this operator.
- Nothing here is hard to copy. The moat, if any, is the discipline of recording
  outcomes and letting them overturn the policy, which is the part most setups skip
  because a system that is never measured always feels like it is working.
