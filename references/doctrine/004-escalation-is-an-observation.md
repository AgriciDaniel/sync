---
type: "doctrine"
title: "004. Escalation Is an Observation"
created: "2026-08-09"
updated: "2026-08-10"
status: "developing"
confidence: "evidence-based"
---

# 004. Escalation Is an Observation

Escalation decided mid-task is escalation decided under sunk cost. Naming the
trigger before starting converts an argument into an observation.

## The six triggers

1. **More than about three files.** The frontier gap widens sharply past three,
   and the weakest models approach zero once a change spans ten or more.
   <https://arxiv.org/abs/2509.16941>
2. **Root-causing rather than localizing.** Agents excel at localizing and fail
   at root cause. <https://arxiv.org/abs/2502.12115>
3. **Horizon beyond roughly an hour of skilled human work.**
4. **Ambiguous requirements** that cannot be pinned down first.
5. **Concurrency, memory model, or subtle shared state.**
6. **Two attempts already failed.** Past attempt two the return curve flattens,
   and six cheap attempts can exceed one frontier attempt.

## Two are machine-checkable, four are not

`sync route --files N --retries N` evaluates triggers 1 and 6. When the requested
role is `implement` or `bulk`, a fired trigger resolves it to `stuck`. Other roles
retain their lane while recording the trigger. That implemented override is
enforcement and is not open to argument.

Triggers 2 to 5 require honest judgment. The failure mode is not misjudging them;
it is never asking. The brief forces the question before work starts.

## The corollary about specification

Trigger 4 is the expensive one, because it is the one that looks like progress.

Underspecification is measurable and costly. On an underspecified variant of
SWE-bench Verified, an uncertainty-aware scaffold that separated
underspecification detection from code execution reached a 69.40% resolve rate,
closing much of the gap with agents given fully specified instructions.
<https://arxiv.org/abs/2603.26233>

That paper does not say what an earlier draft of this note claimed it said. Its
finding is that a capable agent **asks** when the brief is thin, not that a
human must always pre-write the spec. Both routes close the gap; the paper
studied asking.

So the rule is: when the brief cannot be written, either write it at the `spec`
role or let the executor ask before it starts. What is not allowed is proceeding
on an unwritable brief and hoping. That is the trigger.

Caveat: more specification is not automatically better. Adding non-functional
requirements to a prompt decreased Pass@1 by up to 39 percent and raised the
standard deviation from 0.48 to 2.48 against a function-only baseline.
<https://arxiv.org/abs/2503.22851> Aim unambiguous, not exhaustive.

## What this does not prove

The thresholds are borrowed from published studies on other codebases, other task
distributions, and other model generations. Three files is where the gap was
observed to widen, not a constant of nature, and the horizon and retry numbers
are rougher still.

Treat them as defaults to be replaced. Once the outcome ledger holds enough runs,
the trigger values should be re-derived from this operator's own escalation and
pass rates rather than inherited. Until then they are the best available guess
with a source attached, which is not the same as being correct here.

## Related

- [[001. Two Pools Is the Whole Thesis]]
- [[003. A Verdict Is a Command, Not a Claim]]
- [[006. Measure or You Will Believe Anything]]
