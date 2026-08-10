"""Temporary-home integration tests for recoverable Sync installation."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run(*args: str, home: Path, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=ROOT,
        env={**os.environ, "SYNC_BRAIN_INSTALL_HOME": str(home)},
        text=True,
        capture_output=True,
        check=check,
    )


def test_sync_install_revert_restores_settings_and_codex_link() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        home = Path(temporary)
        settings = home / ".claude" / "settings.json"
        settings.parent.mkdir(parents=True)
        original = {"statusLine": {"command": "/usr/local/bin/other"}, "model": "keep"}
        settings.write_text(json.dumps(original) + "\n", encoding="utf-8")

        run("bin/sync-install", "--apply", home=home)
        installed = json.loads(settings.read_text(encoding="utf-8"))
        assert installed["model"] == "keep"
        assert (home / ".codex" / "skills" / "sync").is_symlink()

        run("bin/sync-install", "--revert", home=home)
        assert json.loads(settings.read_text(encoding="utf-8")) == original
        assert not (home / ".codex" / "skills" / "sync").exists()


def test_sync_install_revert_refuses_to_clobber_later_settings_change() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        home = Path(temporary)
        run("bin/sync-install", "--apply", home=home)
        settings = home / ".claude" / "settings.json"
        settings.write_text('{"changed_by_user": true}\n', encoding="utf-8")

        result = run("bin/sync-install", "--revert", home=home, check=False)
        assert result.returncode == 1
        assert "changed after Sync installed" in result.stderr
        assert json.loads(settings.read_text(encoding="utf-8")) == {"changed_by_user": True}


def test_sync_install_refuses_user_owned_codex_target_without_settings_change() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        home = Path(temporary)
        target = home / ".codex" / "skills" / "sync"
        target.mkdir(parents=True)
        (target / "user.txt").write_text("keep", encoding="utf-8")

        result = run("bin/sync-install", "--apply", home=home, check=False)
        assert result.returncode == 1
        assert (target / "user.txt").read_text(encoding="utf-8") == "keep"
        assert not (home / ".claude" / "settings.json").exists()


def test_shell_installer_never_replaces_user_target_and_restores_managed_update() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        home = Path(temporary)
        target = home / ".codex" / "skills" / "sync-brain"
        target.mkdir(parents=True)
        (target / "user.txt").write_text("keep", encoding="utf-8")
        denied = run("bash", "install.sh", "--target", "codex", home=home, check=False)
        assert denied.returncode != 0
        assert (target / "user.txt").read_text(encoding="utf-8") == "keep"

    with tempfile.TemporaryDirectory() as temporary:
        home = Path(temporary)
        run("bash", "install.sh", "--target", "codex", home=home)
        target = home / ".codex" / "skills" / "sync-brain"
        marker = target / ".sync-brain-install-managed"
        marker.write_text("older-sync\n", encoding="utf-8")
        run("bash", "install.sh", "--target", "codex", home=home)
        run("bash", "uninstall.sh", "--target", "codex", home=home)
        assert marker.read_text(encoding="utf-8") == "older-sync\n"


def test_shell_gemini_uninstall_restores_exact_existing_loader() -> None:
    with tempfile.TemporaryDirectory() as temporary:
        home = Path(temporary)
        loader = home / ".gemini" / "GEMINI.md"
        loader.parent.mkdir(parents=True)
        original = "# User configuration\n\n@./other.md\n"
        loader.write_text(original, encoding="utf-8")

        run("bash", "install.sh", "--target", "gemini", home=home)
        assert "sync-brain-install:start" in loader.read_text(encoding="utf-8")
        run("bash", "uninstall.sh", "--target", "gemini", home=home)
        assert loader.read_text(encoding="utf-8") == original
