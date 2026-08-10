#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import stat
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from os import environ
from pathlib import Path
from typing import Iterable, TypedDict


REPO = Path(__file__).resolve().parent.parent
TEXT_SUFFIXES = {
    ".base",
    ".canvas",
    ".css",
    ".csv",
    ".html",
    ".json",
    ".md",
    ".py",
    ".sh",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
}
SKIP_PARTS = {
    ".git",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "venv",
}
SKIP_SUFFIXES = {".pyc", ".pyo", ".log"}
FORBIDDEN_ENTRY_NAMES = {
    ".env",
    ".env.local",
    ".env.production",
    ".DS_Store",
    "Thumbs.db",
    "workspace.json",
}
PUBLIC_FIXTURE_RAW_ROOTS = (
    Path("assets/template-brain/.raw"),
    Path("examples/sample-vault/.raw"),
)
MAX_SCAN_BYTES = 25 * 1024 * 1024
REPRODUCIBLE_ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)
FORBIDDEN_TEXT_PATTERNS = {
    "local home path": re.compile(rb"/home/[A-Za-z0-9_.-]+"),
    "private key": re.compile(rb"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    # These prefixes need a left boundary. Without one the pattern matches inside
    # ordinary hyphenated words: the word "task" followed by "-routing-across-"
    # tripped this scanner on a domain tag containing no secret at all. A secret
    # scanner that cries wolf on prose gets switched off, which is the real
    # failure. Keep example strings out of this file; it scans itself.
    "openai api key": re.compile(rb"(?<![A-Za-z0-9])sk-[A-Za-z0-9_-]{20,}"),
    "anthropic api key": re.compile(rb"(?<![A-Za-z0-9])sk-ant-[A-Za-z0-9_-]{20,}"),
    "github token": re.compile(rb"(ghp|github_pat)_[A-Za-z0-9_]{20,}"),
    "aws key": re.compile(rb"AKIA[0-9A-Z]{16}"),
    "google api key": re.compile(rb"AIza[0-9A-Za-z_-]{20,}"),
    "bearer literal": re.compile(rb"Bearer\s+[A-Za-z0-9._-]{24,}"),
}


class Artifact(TypedDict):
    path: Path
    entries: int


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build verified release ZIP artifacts."
    )
    parser.add_argument("--version", required=True)
    parser.add_argument("--dist-dir", default="dist")
    parser.add_argument(
        "--release-type",
        default="scaffold",
        choices=["scaffold", "demo", "market-ready"],
    )
    args = parser.parse_args(argv)
    version = normalize_version(args.version)
    dist_arg = Path(args.dist_dir)
    dist = (dist_arg if dist_arg.is_absolute() else REPO / dist_arg).resolve()
    if dist == REPO or not dist.is_relative_to(REPO):
        raise SystemExit(f"ERROR: --dist-dir must resolve inside the repo: {dist}")
    dist.mkdir(parents=True, exist_ok=True)
    if args.release_type == "market-ready":
        enforce_market_ready_gate()
    scan_source_tree(exclude_roots=[dist])
    artifacts = [
        build_zip(
            dist / f"sync-brain-template-v{version}.zip",
            REPO / "assets" / "template-brain",
            "sync-brain-template",
        ),
        build_zip(
            dist / f"sync-brain-sample-vault-v{version}.zip",
            REPO / "examples" / "sample-vault",
            "sync-brain-sample-vault",
        ),
        build_source_zip(
            dist / f"sync-brain-source-v{version}.zip",
            version,
            exclude_roots=[dist],
        ),
    ]
    for artifact in artifacts:
        validate_zip(artifact["path"])
    manifest = {
        "product": "sync-brain",
        "version": version,
        "release_type": args.release_type,
        "generated_at": reproducible_timestamp().isoformat(),
        "git_commit": git_commit(),
        "artifacts": [
            {
                "file": a["path"].name,
                "sha256": sha256_file(a["path"]),
                "bytes": a["path"].stat().st_size,
                "entries": a["entries"],
            }
            for a in artifacts
        ],
        "checks": [
            "repo source scan passed",
            "zip entry scan passed",
            "zip content secret scan passed",
            "zip content local-path scan passed",
        ],
    }
    manifest_path = dist / "RELEASE_MANIFEST.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    sums = dist / "SHA256SUMS"
    write_sha256s(sums, [*(a["path"] for a in artifacts), manifest_path])
    validate_sha256s(sums)
    print(f"Release package built in {dist}")
    return 0


def enforce_market_ready_gate() -> None:
    audit = REPO / "scripts" / "audit_brain.py"
    if not audit.exists():
        raise SystemExit(
            "ERROR: market-ready release blocked: missing scripts/audit_brain.py"
        )
    proc = subprocess.run(
        [sys.executable, str(audit), "--require", "market-ready", "--json"],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=False,
    )
    if proc.returncode:
        detail = "\n".join(
            part for part in [proc.stdout.strip(), proc.stderr.strip()] if part
        )
        raise SystemExit("ERROR: market-ready release blocked by audit:\n" + detail)


def normalize_version(value: str) -> str:
    version = value.strip().removeprefix("v")
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        raise SystemExit("ERROR: --version must look like 0.1.0")
    return version


def should_skip(path: Path) -> bool:
    if set(path.parts) & SKIP_PARTS:
        return True
    if any(part.endswith(".egg-info") for part in path.parts):
        return True
    return path.suffix in SKIP_SUFFIXES


def reject_forbidden_entry(path: Path) -> None:
    if path.name in FORBIDDEN_ENTRY_NAMES:
        raise SystemExit(f"ERROR: forbidden release entry: {path.as_posix()}")
    if path.is_absolute() or ".." in path.parts:
        raise SystemExit(f"ERROR: unsafe release entry: {path.as_posix()}")


def iter_tree(root: Path, *, exclude_roots: Iterable[Path] = ()) -> list[Path]:
    resolved_exclusions = tuple(path.resolve() for path in exclude_roots)
    files: list[Path] = []
    for path in root.rglob("*"):
        resolved_path = path.resolve()
        if any(
            resolved_path.is_relative_to(excluded) for excluded in resolved_exclusions
        ):
            continue
        rel = path.relative_to(root)
        if should_skip(rel):
            continue
        reject_forbidden_entry(rel)
        if path.is_symlink():
            raise SystemExit(f"ERROR: symlink not allowed: {rel.as_posix()}")
        if path.is_file():
            files.append(path)
    return sorted(files)


def has_working_git_checkout() -> bool:
    return (
        subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=REPO,
            capture_output=True,
            check=False,
        ).returncode
        == 0
    )


def source_files(*, exclude_roots: Iterable[Path] = ()) -> list[Path]:
    if has_working_git_checkout():
        reject_dirty_tracked_files()
        reject_untracked_files(exclude_roots=exclude_roots)
        proc = subprocess.run(
            ["git", "ls-files", "-z", "--cached"],
            cwd=REPO,
            capture_output=True,
            check=False,
        )
        if proc.returncode != 0:
            raise SystemExit(proc.stderr.decode("utf-8", "replace"))
        files = []
        for raw in proc.stdout.split(b"\0"):
            if raw:
                rel = Path(raw.decode("utf-8", "replace"))
                if should_skip(rel):
                    continue
                reject_forbidden_entry(rel)
                path = REPO / rel
                if any(
                    path.resolve().is_relative_to(excluded.resolve())
                    for excluded in exclude_roots
                ):
                    continue
                if path.is_symlink():
                    raise SystemExit(f"ERROR: symlink not allowed: {rel.as_posix()}")
                if path.is_file():
                    files.append(path)
        return sorted(files)
    return iter_tree(REPO, exclude_roots=exclude_roots)


def reject_dirty_tracked_files() -> None:
    dirty: set[str] = set()
    for args in (
        ["git", "diff", "--name-only", "-z"],
        ["git", "diff", "--name-only", "-z", "--cached"],
    ):
        proc = subprocess.run(args, cwd=REPO, capture_output=True, check=False)
        if proc.returncode != 0:
            raise SystemExit(proc.stderr.decode("utf-8", "replace"))
        dirty.update(
            raw.decode("utf-8", "replace") for raw in proc.stdout.split(b"\0") if raw
        )
    blocked = sorted(path for path in dirty if not should_skip(Path(path)))
    if blocked:
        raise SystemExit(
            "ERROR: dirty tracked files would make release non-reproducible: "
            + ", ".join(blocked[:10])
        )


def reject_untracked_files(*, exclude_roots: Iterable[Path] = ()) -> None:
    proc = subprocess.run(
        ["git", "ls-files", "-z", "--others", "--exclude-standard"],
        cwd=REPO,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        raise SystemExit(proc.stderr.decode("utf-8", "replace"))
    untracked = sorted(
        raw.decode("utf-8", "replace") for raw in proc.stdout.split(b"\0") if raw
    )
    resolved_exclusions = tuple(path.resolve() for path in exclude_roots)
    allowed = [
        path
        for path in untracked
        if not should_skip(Path(path))
        and not any(
            (REPO / path).resolve().is_relative_to(excluded)
            for excluded in resolved_exclusions
        )
    ]
    if allowed:
        raise SystemExit(
            "ERROR: untracked files would make release non-reproducible: "
            + ", ".join(allowed[:10])
        )


def scan_source_tree(*, exclude_roots: Iterable[Path] = ()) -> None:
    for path in source_files(exclude_roots=exclude_roots):
        rel = path.relative_to(REPO)
        if not should_skip(rel):
            scan_file(path, rel.as_posix())


def reproducible_timestamp() -> datetime:
    """Return a source-date timestamp, or a fixed ZIP-safe epoch by default."""
    source_date_epoch = environ.get("SOURCE_DATE_EPOCH")
    if source_date_epoch is None:
        return datetime(1980, 1, 1, tzinfo=timezone.utc)
    try:
        epoch = int(source_date_epoch)
    except ValueError as exc:
        raise SystemExit("ERROR: SOURCE_DATE_EPOCH must be an integer") from exc
    timestamp = datetime.fromtimestamp(epoch, tz=timezone.utc).replace(microsecond=0)
    if timestamp.year < 1980 or timestamp.year > 2107:
        raise SystemExit("ERROR: SOURCE_DATE_EPOCH must be within ZIP timestamp range")
    return timestamp


def zip_info(name: str, source: Path) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(name, date_time=REPRODUCIBLE_ZIP_TIMESTAMP)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.create_system = 3
    info.external_attr = (stat.S_IMODE(source.stat().st_mode) & 0o777) << 16
    return info


def write_zip_entry(zf: zipfile.ZipFile, path: Path, name: str) -> None:
    zf.writestr(
        zip_info(name, path), path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED
    )


def validate_public_raw_source(path: Path) -> None:
    """Allow only fixture-declared raw material bundled with the public demos."""
    try:
        rel = path.resolve().relative_to(REPO)
    except ValueError as exc:
        raise SystemExit(
            f"ERROR: raw release entry is outside the repository: {path}"
        ) from exc
    matching = [root for root in PUBLIC_FIXTURE_RAW_ROOTS if rel.is_relative_to(root)]
    if not matching:
        raise SystemExit(
            f"ERROR: non-fixture raw material cannot be released: {rel.as_posix()}"
        )
    manifest_path = REPO / matching[0] / ".manifest.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise SystemExit(
            f"ERROR: invalid public fixture manifest: {manifest_path}"
        ) from exc
    sources = manifest.get("sources", []) if isinstance(manifest, dict) else []
    if not isinstance(sources, list) or any(
        not isinstance(item, dict) or item.get("source_type") != "fixture"
        for item in sources
    ):
        raise SystemExit(
            f"ERROR: public raw manifest contains a non-fixture source: {manifest_path}"
        )


def allowed_archive_raw_path(path: Path) -> bool:
    parts = path.parts
    if ".raw" not in parts:
        return True
    tail = parts[1:]
    return (
        (
            parts[0] in {"sync-brain-template", "sync-brain-sample-vault"}
            and tail[:1] == (".raw",)
        )
        or tail[:3] == ("assets", "template-brain", ".raw")
        or tail[:3] == ("examples", "sample-vault", ".raw")
    )


def build_zip(out: Path, source: Path, root_name: str) -> Artifact:
    entries = 0
    with zipfile.ZipFile(
        out,
        "w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9,
        strict_timestamps=True,
    ) as zf:
        for path in iter_tree(source):
            if ".raw" in path.parts:
                validate_public_raw_source(path)
            write_zip_entry(
                zf, path, (Path(root_name) / path.relative_to(source)).as_posix()
            )
            entries += 1
    return {"path": out, "entries": entries}


def build_source_zip(
    out: Path, version: str, *, exclude_roots: Iterable[Path] = ()
) -> Artifact:
    entries = 0
    with zipfile.ZipFile(
        out,
        "w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9,
        strict_timestamps=True,
    ) as zf:
        for path in source_files(exclude_roots=exclude_roots):
            rel = path.relative_to(REPO)
            if not should_skip(rel):
                if ".raw" in rel.parts:
                    validate_public_raw_source(path)
                write_zip_entry(
                    zf, path, (Path(f"sync-brain-v{version}") / rel).as_posix()
                )
                entries += 1
    return {"path": out, "entries": entries}


def validate_zip(path: Path) -> None:
    with zipfile.ZipFile(path) as zf:
        names = zf.namelist()
        if not names:
            raise SystemExit(f"ERROR: empty artifact: {path.name}")
        for name in names:
            rel = Path(name)
            for part in rel.parts:
                reject_forbidden_entry(Path(part))
            if should_skip(rel) or any(part in SKIP_PARTS for part in rel.parts):
                raise SystemExit(f"ERROR: forbidden zip entry in {path.name}: {name}")
            if not allowed_archive_raw_path(rel):
                raise SystemExit(f"ERROR: non-fixture raw entry in {path.name}: {name}")
            mode = zf.getinfo(name).external_attr >> 16
            if stat.S_ISLNK(mode):
                raise SystemExit(f"ERROR: symlink entry in {path.name}: {name}")
            scan_bytes(zf.read(name), f"{path.name}:{name}", rel.suffix)


def scan_file(path: Path, label: str) -> None:
    size = path.stat().st_size
    if size > MAX_SCAN_BYTES:
        raise SystemExit(f"ERROR: file too large for release scan: {label}")
    scan_bytes(path.read_bytes(), label, path.suffix)


def scan_bytes(data: bytes, label: str, suffix: str) -> None:
    if suffix and suffix not in TEXT_SUFFIXES:
        return
    for name, pattern in FORBIDDEN_TEXT_PATTERNS.items():
        if pattern.search(data):
            raise SystemExit(f"ERROR: {name} found in {label}")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_sha256s(path: Path, artifacts: list[Path]) -> None:
    path.write_text(
        "\n".join(f"{sha256_file(a)}  {a.name}" for a in artifacts) + "\n",
        encoding="utf-8",
    )


def validate_sha256s(path: Path) -> None:
    for line in path.read_text(encoding="utf-8").splitlines():
        expected, filename = line.split("  ", 1)
        actual = sha256_file(path.parent / filename)
        if expected != actual:
            raise SystemExit(f"ERROR: checksum mismatch for {filename}")


def git_commit() -> str | None:
    if not has_working_git_checkout():
        return None
    proc = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=False,
    )
    return proc.stdout.strip() if proc.returncode == 0 else None


if __name__ == "__main__":
    raise SystemExit(main())
