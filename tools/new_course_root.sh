#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-}"
if [[ -z "${ROOT}" ]]; then
  read -rp "Root folder to create: " ROOT
fi

mkdir -p "${ROOT}"
cd "${ROOT}"

if [[ ! -d course-commons ]]; then
  read -rp "Clone course-commons? (y/N): " ans
  if [[ "${ans,,}" == y* ]]; then
    read -rp "course-commons Git URL (e.g., git@github.com:langd0n-classes/course-commons.git): " URL
    git clone "${URL}" course-commons
  fi
fi

read -rp "Course repo to clone (org/name or full URL, empty to skip): " COURSE
if [[ -n "${COURSE}" ]]; then
  if [[ "${COURSE}" == http* || "${COURSE}" == git@* ]]; then
    git clone "${COURSE}"
    REPO_DIR="$(basename "${COURSE%.git}")"
  else
    git clone "git@github.com:${COURSE}.git"
    REPO_DIR="$(basename "${COURSE}")"
  fi
  # Ensure .instructor exists in the course repo
  touch "${REPO_DIR}/.instructor" || true
fi

echo "Done. Layout:"
ls -la
