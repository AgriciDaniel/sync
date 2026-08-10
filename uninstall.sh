#!/usr/bin/env bash
set -euo pipefail

target="codex"
custom_path=""
while [ "$#" -gt 0 ]; do
  case "$1" in
    --target) target="${2:?}"; shift 2 ;;
    --path) custom_path="${2:?}"; shift 2 ;;
    -h|--help) echo "Usage: ./uninstall.sh [--target codex|claude|agents|gemini|openclaw|portable|custom|all] [--path DIR]"; exit 0 ;;
    *) echo "ERROR: unknown argument: $1" >&2; exit 2 ;;
  esac
done

case "${target}" in codex|claude|agents|gemini|openclaw|portable|custom|all) ;; *) echo "ERROR: invalid target" >&2; exit 2 ;; esac
if [ "${target}" = "custom" ] && [ -z "${custom_path}" ]; then
  echo "ERROR: --target custom requires --path" >&2
  exit 2
fi
base_home="${SYNC_BRAIN_INSTALL_HOME:-${HOME}}"
state_dir="${base_home}/.sync-brain-installer"
managed_marker=".sync-brain-install-managed"

target_dir() {
  case "$1" in
    codex) echo "${base_home}/.codex/skills/sync-brain" ;;
    claude) echo "${base_home}/.claude/skills/sync-brain" ;;
    agents) echo "${base_home}/.agents/skills/sync-brain" ;;
    openclaw) echo "${base_home}/.openclaw/skills/sync-brain" ;;
    portable) echo "${base_home}/.agent-skills/sync-brain" ;;
    custom) echo "${custom_path%/}/sync-brain" ;;
  esac
}

remove_one() {
  local dir="$1" name="$2" backup=""
  if [ -e "${dir}" ] || [ -L "${dir}" ]; then
    if [ ! -f "${dir}/${managed_marker}" ]; then
      echo "ERROR: refusing to remove user-owned target: ${dir}" >&2
      return 1
    fi
    if [ -d "${state_dir}/backups" ]; then
      backup="$(find "${state_dir}/backups" -mindepth 2 -maxdepth 2 -type d -name "${name}" -print 2>/dev/null | sort | tail -n 1)"
    fi
    rm -rf -- "${dir}"
    if [ -n "${backup}" ]; then
      mkdir -p "$(dirname "${dir}")"
      mv -- "${backup}" "${dir}"
      echo "Restored previous Sync installation at ${dir}"
    else
      echo "Removed ${dir}"
    fi
  else
    echo "Sync is not installed at ${dir}"
  fi
}

assert_removable() {
  local dir="$1"
  if { [ -e "${dir}" ] || [ -L "${dir}" ]; } && [ ! -f "${dir}/${managed_marker}" ]; then
    echo "ERROR: refusing to remove user-owned target: ${dir}" >&2
    return 1
  fi
}

remove_gemini() {
  local dir="${base_home}/.gemini/sync-brain"
  local loader="${base_home}/.gemini/GEMINI.md"
  remove_one "${dir}" "gemini"
  if [ -f "${loader}" ]; then
    local loader_backup=""
    if [ -d "${state_dir}/backups" ]; then
      loader_backup="$(find "${state_dir}/backups" -mindepth 2 -maxdepth 2 -type f -name 'gemini-loader.md' -print 2>/dev/null | sort | tail -n 1)"
    fi
    if [ -n "${loader_backup}" ]; then
      cp -- "${loader_backup}" "${loader}"
      echo "Restored Gemini loader at ${loader}"
      return
    fi
    python - "${loader}" <<'PY'
from __future__ import annotations

import re
import sys
from pathlib import Path

path = Path(sys.argv[1])
start = "<!-- sync-brain-install:start -->"
end = "<!-- sync-brain-install:end -->"
text = path.read_text(encoding="utf-8")
pattern = f"\n*{re.escape(start)}.*?{re.escape(end)}\n*"
new_text = re.sub(pattern, "\n", text, flags=re.S).strip()
if new_text:
    path.write_text(new_text + "\n", encoding="utf-8")
else:
    path.unlink()
PY
    echo "Sync Gemini loader cleaned at ${loader}"
  fi
}

if [ "${target}" = "all" ]; then
  for name in codex claude agents openclaw portable; do
    assert_removable "$(target_dir "${name}")"
  done
  assert_removable "${base_home}/.gemini/sync-brain"
  for name in codex claude agents openclaw portable; do
    remove_one "$(target_dir "${name}")" "${name}"
  done
  remove_gemini
elif [ "${target}" = "gemini" ]; then
  assert_removable "${base_home}/.gemini/sync-brain"
  remove_gemini
else
  assert_removable "$(target_dir "${target}")"
  remove_one "$(target_dir "${target}")" "${target}"
fi
