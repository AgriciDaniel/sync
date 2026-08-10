---
type: "doctrine"
title: "003. A Verdict Is a Command, Not a Claim"
created: "2026-08-09"
updated: "2026-08-10"
status: "developing"
confidence: "evidence-based"
---

# 003. A Verdict Is a Command, Not a Claim

The gate is what makes a cheaper lane safe. Without it, routing work to a cheaper
pool just moves the place where confident wrong answers are produced.

## Evidence

Self-repair using the model's own feedback succeeded 33.30%; with real external
feedback, 52.60%. <https://arxiv.org/abs/2306.09896>

Asking a model whether its own work was good is the documented failure mode, not
the safeguard.

## The ladder, strongest and cheapest first

1. Compile or type check. Non-negotiable and free.
2. Lint with the project's own configuration.
3. A reproduction script written **before** the fix, re-run after.
4. The real test suite, run to completion.
5. Fresh-context reviewer seeing only the diff.

Stop on the first hard failure. There is no information in running the suite
while the type check is red.

## Three results, and the third is the one people get wrong

- `pass` executed evidence supports the criterion
- `fail` executed evidence contradicts the criterion
- `inconclusive` the runner is absent, a configured no-evidence exit fired, or
  the available checks cannot settle the criterion

An inconclusive result is not a pass. `pytest` exiting 5 means no tests were collected, which is
"this produced no evidence either way," not "the checks passed." A project with
no tests has not been tested however green the summary looks. Sync records the
reason so a report cannot quietly round it up.

## Enforcement

The ladder runs as a Stop hook. A non-pass returns exit code 2 and a bounded
redacted diagnostic tail, which blocks turn-end. Missing or malformed hook input
and `stop_hook_active` exit 0 to avoid a self-blocking loop. The explicit
`SYNC_ALLOW_UNVERIFIED_STOP=1` operator override also exits 0 while preserving
the non-pass verdict. Other nonzero hook exit codes do not block, which is the
most common way a policy hook silently does nothing.
<https://code.claude.com/docs/en/hooks>

Official guidance points the same way: give the agent a check it can run, and
gate harder with a Stop hook or a fresh-context verifier.
<https://code.claude.com/docs/en/best-practices>

Both exit-code behaviours were confirmed live against `bin/sync gate --hook`
during Sync's build rather than taken on trust.

## What this does not prove

A gate bounds correctness against the checks that exist. It says nothing about
the checks that were never written. A green ladder on a thin suite is weak
evidence, and Sync reports the skips precisely so that weakness stays visible.

## Related

- [[001. Two Pools Is the Whole Thesis]]
- [[002. The Council Is Two Meters, Not Two Opinions]]
- [[005. Enforcement Beats Prose]]
