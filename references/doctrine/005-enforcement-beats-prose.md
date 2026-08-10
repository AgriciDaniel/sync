---
type: "doctrine"
title: "005. Enforcement Beats Prose"
created: "2026-08-09"
updated: "2026-08-09"
status: "developing"
confidence: "evidence-based"
---

# 005. Enforcement Beats Prose

The reason Sync is scripts and hooks rather than a long instruction file.

## The evidence that instruction-level routing fails

The highest-rated cheap-routing setup circulating in the community was tested by
asking the model to self-report compliance. The result: "Compliance was poor. I
used the Explore subagent but I didn't use ask-kimi, kimi-write, or extract-chat
at any point."

The author's own diagnosis: "Claude Code's built-in instructions tell it to
prefer its native Read tool over Bash commands. Our CLAUDE.md rules are fighting
against that default."

A rule in prose competes with the system prompt and loses. Official docs draw the
same line: hooks are deterministic and "guarantee the action happens," unlike
advisory instructions. <https://code.claude.com/docs/en/hooks>

The same guidance treats runnable checks as the primary quality mechanism rather
than instructions about quality. <https://code.claude.com/docs/en/best-practices>

## Where each decision belongs

| Decision | Layer |
|---|---|
| Which lane a role resolves to | `routing-policy.json`, read by scripts |
| Whether a trigger fired | `sync route`, which records every trigger and promotes `implement` or `bulk` to `stuck` |
| Whether work passed | Stop hook running the ladder, exit 2 to block |
| Which model a subagent uses | per-agent frontmatter, not prose |
| What a task means | the model, which is what it is good at |

## The hook hazard

Hooks are the least portable artifact in the system. They depend on host-set
environment variables and on a payload shape that differs between harnesses. A
hook whose path resolves but whose payload assumptions are wrong **loads
successfully and misbehaves silently**, which is worse than a clean failure.

Never emulate another harness's event payload to make a hook load. Exclude it
instead. Sync's gate reads `stop_hook_active` defensively and degrades to exit 0
when the payload is absent or unparseable, because a gate that blocks on its own
confusion is worse than no gate.

## The generator hazard, learned the hard way

A directory with two owners has one owner. `scripts/synthesize_brain.py` deletes
every markdown file in `references/canon/` and regenerates it from the source
ledger. Hand-written doctrine placed there is destroyed the first time anyone
populates the ledger and runs the pipeline.

This is not hypothetical. It destroyed twelve doctrine notes in a sibling brain,
and then destroyed seven of these notes during Sync's own build. That is why
doctrine lives in `references/doctrine/`, which no generator writes to.

Generated and authored content must never share a directory.

## The limit of this rule

Enforcement cannot classify. Deciding that a task is `implement` rather than
`spec` is judgment, and pushing judgment into a script produces brittle keyword
matching that fails in both directions. Sync draws the line deliberately: the
model classifies, the script enforces.

## Related

- [[003. A Verdict Is a Command, Not a Claim]]
- [[004. Escalation Is an Observation]]
- [[007. The Autonomy Boundary]]
