#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: ./install.sh [--target codex|claude|agents|gemini|openclaw|portable|custom|all] [--path DIR]

Installs the Sync skill surface.
Use --target custom --path <agent-skill-root> for Hermes or another runtime
when its official skill root is known.
Set SYNC_BRAIN_INSTALL_HOME to test against a temporary home directory.
USAGE
}

target="codex"
custom_path=""
while [ "$#" -gt 0 ]; do
  case "$1" in
    --target) target="${2:?}"; shift 2 ;;
    --path) custom_path="${2:?}"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "ERROR: unknown argument: $1" >&2; usage >&2; exit 2 ;;
  esac
done

case "${target}" in codex|claude|agents|gemini|openclaw|portable|custom|all) ;; *) echo "ERROR: invalid target" >&2; exit 2 ;; esac
if [ "${target}" = "custom" ] && [ -z "${custom_path}" ]; then
  echo "ERROR: --target custom requires --path" >&2
  exit 2
fi

source_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
base_home="${SYNC_BRAIN_INSTALL_HOME:-${HOME}}"
state_dir="${base_home}/.sync-brain-installer"
transaction_id="$(date +%Y%m%d-%H%M%S)-$$"
backup_dir="${state_dir}/backups/${transaction_id}"
declare -a committed_destinations=()
declare -A destination_backups=()
gemini_loader=""
gemini_loader_backup=""
gemini_loader_was_absent="false"

managed_marker=".sync-brain-install-managed"

rollback() {
  local dest backup
  if [ -n "${gemini_loader}" ] && [ -n "${gemini_loader_backup}" ]; then
    if [ "${gemini_loader_was_absent}" = "true" ]; then
      rm -f -- "${gemini_loader}"
    elif [ -f "${gemini_loader_backup}" ]; then
      cp -- "${gemini_loader_backup}" "${gemini_loader}"
    fi
  fi
  for dest in "${committed_destinations[@]:-}"; do
    backup="${destination_backups["${dest}"]:-}"
    [ -e "${dest}" ] || [ -L "${dest}" ] || continue
    rm -rf -- "${dest}"
    if [ -n "${backup}" ] && [ -d "${backup}" ]; then
      mv -- "${backup}" "${dest}"
    fi
  done
}

trap 'rollback' ERR

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

copy_tree() {
  local src="$1" dest="$2"
  mkdir -p "${dest}"
  (cd "${src}" && find . -type f ! -path '*/__pycache__/*' ! -name '*.pyc' -print0 | while IFS= read -r -d '' file; do
    mkdir -p "${dest}/$(dirname "${file}")"
    cp "${file}" "${dest}/${file}"
  done)
}

install_one() {
  local dest="$1" name="$2" parent stage backup=""
  parent="$(dirname "${dest}")"
  if [ -e "${dest}" ] || [ -L "${dest}" ]; then
    if [ ! -f "${dest}/${managed_marker}" ]; then
      echo "ERROR: refusing to replace user-owned target: ${dest}" >&2
      echo "Move it aside yourself, then retry." >&2
      return 1
    fi
    backup="${backup_dir}/${name}"
    mkdir -p "${backup_dir}"
    mv -- "${dest}" "${backup}"
  fi
  committed_destinations+=("${dest}")
  destination_backups["${dest}"]="${backup}"
  mkdir -p "${parent}"
  stage="$(mktemp -d "${parent}/.sync-brain-stage.XXXXXX")"
  for file in SKILL.md AGENTS.md CLAUDE.md GEMINI.md README.md LICENSE CHANGELOG.md RELEASE_CHECKLIST.md PUBLISHING_NOTICE.md; do
    if [ -f "${source_dir}/${file}" ]; then
      cp "${source_dir}/${file}" "${stage}/${file}"
    fi
  done
  if [ -d "${source_dir}/agents" ]; then
    copy_tree "${source_dir}/agents" "${stage}/agents"
  fi
  copy_tree "${source_dir}/scripts" "${stage}/scripts"
  copy_tree "${source_dir}/assets/template-brain" "${stage}/assets/template-brain"
  copy_tree "${source_dir}/references" "${stage}/references"
  copy_tree "${source_dir}/docs" "${stage}/docs"
  printf 'sync-brain\n' > "${stage}/${managed_marker}"
  chmod -R go-rwx "${stage}"
  mv -- "${stage}" "${dest}"
  echo "Sync installed to ${dest}"
}

install_gemini() {
  local dest="${base_home}/.gemini/sync-brain"
  local loader="${base_home}/.gemini/GEMINI.md"
  install_one "${dest}" "gemini"
  mkdir -p "$(dirname "${loader}")"
  mkdir -p "${backup_dir}"
  gemini_loader="${loader}"
  gemini_loader_backup="${backup_dir}/gemini-loader.md"
  if [ -f "${loader}" ]; then
    cp -- "${loader}" "${gemini_loader_backup}"
  else
    gemini_loader_was_absent="true"
  fi
  python - "${loader}" "@./sync-brain/GEMINI.md" <<'PY'
from __future__ import annotations

import re
import sys
from pathlib import Path

path = Path(sys.argv[1])
import_line = sys.argv[2]
start = "<!-- sync-brain-install:start -->"
end = "<!-- sync-brain-install:end -->"
block = f"{start}\n{import_line}\n{end}"
text = path.read_text(encoding="utf-8") if path.exists() else ""
pattern = f"{re.escape(start)}.*?{re.escape(end)}"
if re.search(pattern, text, flags=re.S):
    text = re.sub(pattern, block, text, flags=re.S)
else:
    text = (text.rstrip() + "\n\n" + block + "\n").lstrip()
path.write_text(text, encoding="utf-8")
PY
  echo "Sync Gemini loader updated at ${loader}"
}

if [ "${target}" = "all" ]; then
  for name in codex claude agents openclaw portable; do
    install_one "$(target_dir "${name}")" "${name}"
  done
  install_gemini
elif [ "${target}" = "gemini" ]; then
  install_gemini
else
  install_one "$(target_dir "${target}")" "${target}"
fi

trap - ERR
