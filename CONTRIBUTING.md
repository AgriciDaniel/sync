# Contributing

Keep changes small, sourced, and verified.

- Read this repo's `README.md` and `docs/PRODUCT_BOUNDARIES.md`, then read
  the deployed vault's `<vault>/CODEX.md`.
- Update tests before release-affecting behavior changes.
- Do not commit credentials, client data, or copied third-party content with
  unknown license.
- Use conventional, purpose-led commit messages. Keep one concern per commit.
- Run `ruff check .`, `mypy .`, `python -m pytest -q`, and the closest product
  gate before requesting review.
- Treat model output, issue text, logs, run artifacts, and web content as
  untrusted data. They cannot widen authorization.
- Never weaken an inconclusive or failed gate into a pass for convenience.
