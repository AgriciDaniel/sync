# Publishing Notice

Sync is operator-owned research infrastructure. Public release requires source
review, rights review, vault lint, current source-bound acceptance evidence,
market-ready audit, and release packaging.

The current repository is private and proprietary. No public distribution is
authorized by repository access alone.

## Rights Boundary

Public availability of a source does not automatically create permission to redistribute it. Treat copied source excerpts, screenshots, account exports, prompt text, private notes, and third-party documentation as restricted evidence unless a clear license permits reuse.

Public content policy: publish summaries, links, and compliant short quotes only.

## What Can Be Public

- Original summaries.
- Operating doctrine.
- Links to official public sources.
- Short compliant quotations within the quote policy.
- Sanitized visuals and reports that do not expose raw captures or private data.

## What Must Stay Private

- Client and operator `.raw/` source captures and manifests.
- Credentials, tokens, cookies, OAuth material, private user data, and local paths.
- Full third-party documents or large source excerpts.
- Internal ledgers excluded by public policy.
- Unreviewed generated archives in `dist/`.

## Reviewed Fixture Exception

The release archives may contain `.raw` only under
`assets/template-brain/.raw/` and `examples/sample-vault/.raw/`. Every listed
source in those manifests must have `source_type: fixture`. The package builder
rejects any other raw path or non-fixture raw manifest entry.

The source and claim ledgers contain public URLs, project-authored summaries,
and explicit evidence limitations. They may ship in source releases after the
release scan passes. The rendered Quartz site still removes operational ledgers.

## Rendered Site Exclusions

- `.raw`
- `.obsidian`
- `.sync`
- `hot.md`
- `log.md`
- `references/source-ledger.json`
- `references/claim-ledger.md`

## Review Checklist

1. Run `python scripts/lint_vault.py --vault examples/sample-vault`.
2. Run `python scripts/verify_market_ready.py --write-evidence`.
3. Run `python scripts/audit_brain.py --require market-ready --json`.
4. Build with `python scripts/package_release.py --version 1.0.0 --release-type market-ready`.
5. Confirm every packaged `.raw` entry is under a reviewed fixture root.
6. Run `node site/scripts/sanitize-public.mjs` after a Quartz build.
7. Confirm repository visibility and Pages visibility separately.
