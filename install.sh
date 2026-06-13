#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_NAME="$(basename "${PROJECT_DIR}")"
VENV_DIR="${VENV_DIR:-${HOME}/venv/${PROJECT_NAME}}"
PYTHON_BIN="${PYTHON_BIN:-}"
if [ -z "${PYTHON_BIN}" ]; then
  if command -v python3.11 >/dev/null 2>&1; then
    PYTHON_BIN=python3.11
  else
    PYTHON_BIN=python3
  fi
fi

cd "${PROJECT_DIR}"

if ! command -v uv >/dev/null 2>&1; then
  if command -v python3 >/dev/null 2>&1; then
    python3 -m pip install --user --upgrade uv
  else
    echo "python3 is required to install uv" >&2
    exit 1
  fi
fi

mkdir -p "$(dirname "${VENV_DIR}")"
uv venv --python "${PYTHON_BIN}" "${VENV_DIR}"
uv pip install --python "${VENV_DIR}/bin/python" --upgrade -r requirements.txt

if [ ! -f ".env" ] && [ -f ".env.example" ]; then
  cp .env.example .env
  chmod 600 .env
fi

cat <<MSG
Installed ${PROJECT_NAME} into ${VENV_DIR}
Next:
  1. Edit ${PROJECT_DIR}/.env and set API_TOKEN
  2. source ${PROJECT_DIR}/run.sh 0.0.0.0 8088
MSG
