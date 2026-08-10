# Third-Party Notices

Sync's Python source, shell scripts, Markdown doctrine, and generated SVG assets
are original project material unless a file says otherwise.

The Claude and Codex marks under `assets/brand/` were supplied by the project
owner for nominative identification of compatible execution lanes. They are not
original Sync artwork, are not covered by Sync's proprietary project license,
and remain subject to their respective owners' trademark and brand terms. Their
use does not imply partnership, sponsorship, or endorsement.

The repository links to and summarizes research papers and vendor documentation.
Those external works are not redistributed in the release archives. Their titles,
URLs, retrieval dates, claim scope, and non-proof boundaries are recorded in
`references/source-ledger.json`.

Development and test dependencies are installed separately and are not vendored
in Sync release archives:

- `pytest`, MIT License.
- `jsonschema`, MIT License.
- `ruff` and `mypy`, installed as development tools and not redistributed.
- Quartz v4, used only when an operator installs the optional site dependency.
  Quartz code is not vendored in this repository or the Python package.

Downstream distributors remain responsible for preserving notices required by
any dependencies they choose to bundle.
