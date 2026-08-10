# Product Boundaries

Sync combines an advisory, read-only Obsidian brain with a run-bound local
execution harness for Claude and Codex council orchestration: task routing across
billing pools, artifact-mediated coordination, ground-truth verification gates,
quota and cost measurement, and policy evolution from recorded outcomes.

## It Does

- Preserve raw sources under `.raw/`.
- Synthesize source-cited notes and deliverables.
- Import fingerprint-bound Sync run directories into sanitized normalized
  records and cited vault reports.
- Maintain action queues, reports, and next actions.
- Keep decisions auditable through source links and rollback notes.
- Gate maturity through `references/source-ledger.json`,
  `references/adapter-manifest.json`, and `scripts/audit_brain.py`.
- Permit reversible workspace-local edits only through a bounded run whose
  project, route, dispatch, structured result, and verdict are fingerprint-bound.
- Execute gate commands in a network-isolated Bubblewrap sandbox on supported
  Linux systems, with a private home, a narrow read-only runtime allowlist, only
  the bound project and a private temporary directory writable, and `.git`
  remounted read-only.

## It Does Not

- No capacity-relief claim unless source and destination have distinct declared
  pool IDs, observed non-secret authentication modes, and current headroom
  recorded as available
- No price, quota, or benchmark number without a dated source and the plan or harness it applies to
- No gate result reported from model judgment; a verdict requires a command, an exit code, and captured output
- No commit, push, publish, deploy, spend, account change, or production change without explicit owner approval
- No intentional credential persistence. Runtime evidence uses environment
  scrubbing, narrow runtime mounts, a private home, and deterministic best-effort
  redaction; these controls do not prove arbitrary output is secret-free
- No claim of measured improvement without naming the baseline and the measurement
- No unsandboxed gate or project-defined gate execution without an explicit
  operator override bound to the exact project gate file

## Safety Risks

- A council amplifying confident error when the verifier is weaker than the work
- Autonomy escaping the workspace envelope into irreversible or outward-facing actions
- Stale prices, quotas, and model rosters driving a routing decision that no longer holds
- Secrets leaking into run directories, evidence captures, or the outcome ledger
- Untrusted tool output and inter-agent messages read as instructions
- Delegation added for its own sake, reproducing the measured double-context penalty

## Maturity Boundary

Maturity is enforced in stages. Market-ready quality requires current research,
an executed domain adapter, deterministic demo verification, source citations,
Obsidian graph hygiene, an explicit distribution license, and source-bound
acceptance evidence. Any source change invalidates the recorded release evidence
until the suite is executed again.
