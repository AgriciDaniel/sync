---
type: "reference"
title: "Sync Doctrine"
created: "2026-08-09"
updated: "2026-08-09"
status: "active"
---

# Sync Doctrine

Seven notes. Each states a decision Sync enforces, the evidence behind it, and
what that evidence does not prove.

## Why this is not in `references/canon/`

`scripts/synthesize_brain.py` deletes every markdown file in `references/canon/`
and regenerates it from `references/source-ledger.json`. That directory is
generator-owned output, not an authoring surface.

Hand-written doctrine placed there is destroyed the first time anyone populates
the ledger and runs the pipeline. That is not a hypothetical: it removed twelve
doctrine notes from a sibling brain, and it removed seven of these notes during
Sync's own build before they were moved here.

`references/canon/` holds folded source captures. `references/doctrine/` holds
authored decisions. Generated and authored content do not share a directory.

## Ledger

| # | Note | Confidence | Enforced by |
|---|---|---|---|
| 001 | [Two Pools Is the Whole Thesis](001-two-pools-is-the-whole-thesis.md) | practitioner | `routing-policy.json` pool table |
| 002 | [The Council Is Two Meters, Not Two Opinions](002-the-council-is-two-meters-not-two-opinions.md) | contested | run directory topology |
| 003 | [A Verdict Is a Command, Not a Claim](003-a-verdict-is-a-command-not-a-claim.md) | evidence-based | `sync gate`, Stop hook exit 2 |
| 004 | [Escalation Is an Observation](004-escalation-is-an-observation.md) | evidence-based | `sync route` trigger override |
| 005 | [Enforcement Beats Prose](005-enforcement-beats-prose.md) | evidence-based | the existence of `bin/` |
| 006 | [Measure or You Will Believe Anything](006-measure-or-you-will-believe-anything.md) | evidence-based | `sync record`, `sync evolve` |
| 007 | [The Autonomy Boundary](007-the-autonomy-boundary.md) | practitioner | `autonomy_envelope` in policy |

This index is checked against disk in both directions by
`tests/test_canon_index.py`.

## Substance scoring

Run it with the ledger, or the number is meaningless:

```bash
python3 score_substance.py --vault references/doctrine \
  --note-type doctrine --ledger references/source-ledger.json
```

Omitting `--ledger` reports citation coverage 0.00 no matter how well sourced
the notes are, because the scanner resolves cited URLs against the ledger and
silently finds none. That misreading happened once during this brain's own
audit and was caught only by asking why a fix changed nothing.

Current: **substance score 92**, no near-duplicates, no generic bundle reuse,
skeleton reuse 1.

## Residual findings, accepted rather than padded

Citation coverage sits at 0.71 against a 0.95 floor. Two notes carry fewer than
two ledger-resolvable sources, and that is deliberate:

- **006** rests on a single randomized trial and says so in its own text. A
  second citation would have to be tangential, and attaching one to lift a
  coverage number is precisely the defect this brain exists to catch.
- **007** is a policy decision about where autonomy stops, not an empirical
  claim. It has no external source because there is nothing external to cite.

Table and procedure coverage sits at 0.71 against a 0.90 floor. That floor is
calibrated for research spokes; several of these notes are arguments rather than
procedures, and a table added to clear a threshold carries no information.

What the same audit did fix, because these were real: two citations carried
descriptive titles invented by the author rather than the papers' actual titles,
and three numeric claims that do not appear in their cited sources were removed
or demoted. See `references/source-ledger.json`.

## Provenance

Adapted and extended from the twelve-note canon in Agent Ops Brain, narrowed to
the Claude and Codex two-pool case and rewritten so each note names the control
that enforces it.
