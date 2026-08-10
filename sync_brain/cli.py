from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from sync_brain.adapters.sync_run import AdapterError, import_run


REPO = Path(__file__).resolve().parent.parent
PY = sys.executable


def run_script(script: str, args: list[str]) -> int:
    return subprocess.call([PY, str(REPO / "scripts" / script), *args], cwd=REPO)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="sync-brain", description="Operate Sync.")
    sub = parser.add_subparsers(dest="command", required=True)
    p_new = sub.add_parser("new")
    p_new.add_argument("client")
    p_new.add_argument("--client-name", default="")
    p_new.add_argument("--owner", default="Daniel Agrici")
    p_new.add_argument("--out-dir", default="~/sync-brain-vaults")
    p_ingest = sub.add_parser("ingest")
    p_ingest.add_argument("--vault", required=True)
    p_ingest.add_argument("--file", required=True)
    p_import_run = sub.add_parser(
        "import-run", description="Import one fingerprint-bound Sync run into a vault."
    )
    p_import_run.add_argument("--vault", required=True)
    p_import_run.add_argument("--run-dir", required=True)
    p_synth = sub.add_parser("synthesize")
    p_synth.add_argument("--vault", required=True)
    p_report = sub.add_parser("report")
    p_report.add_argument("--vault", required=True)
    p_report.add_argument("--out", default="")
    p_report.add_argument("--html-only", action="store_true")
    p_visuals = sub.add_parser("visuals")
    p_visuals.add_argument("--vault", required=True)
    p_lint = sub.add_parser("lint")
    p_lint.add_argument("--vault", required=True)
    p_lint.add_argument("--template", action="store_true")
    p_next = sub.add_parser("next")
    p_next.add_argument("--vault", required=True)
    sub.add_parser("demo")
    args = parser.parse_args(argv)
    if args.command == "new":
        call = [
            "--client",
            args.client,
            "--client-name",
            args.client_name or args.client,
            "--owner",
            args.owner,
            "--out-dir",
            args.out_dir,
        ]
        return run_script("scaffold_vault.py", call)
    if args.command == "ingest":
        return run_script(
            "ingest_source.py", ["--vault", args.vault, "--file", args.file]
        )
    if args.command == "import-run":
        try:
            raw_path, report_path = import_run(args.vault, args.run_dir)
        except (AdapterError, OSError) as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 2
        print(f"Imported normalized run: {raw_path}")
        print(f"Rendered cited report: {report_path}")
        return 0
    if args.command == "synthesize":
        return run_script("synthesize_brain.py", ["--vault", args.vault])
    if args.command == "report":
        call = ["--vault", args.vault]
        if args.out:
            call += ["--out", args.out]
        if args.html_only:
            call.append("--html-only")
        return run_script("render_brain_report.py", call)
    if args.command == "visuals":
        return run_script("generate_vault_visuals.py", ["--vault", args.vault])
    if args.command == "lint":
        call = ["--vault", args.vault]
        if args.template:
            call.append("--template")
        return run_script("lint_vault.py", call)
    if args.command == "next":
        return run_script("guide_next_action.py", ["--vault", args.vault])
    if args.command == "demo":
        return run_script("build_demo_vault.py", [])
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
