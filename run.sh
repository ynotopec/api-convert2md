#!/usr/bin/env bash
set -Eeuo pipefail

HOST="${1:-${HOST:-${SERVER_NAME:-0.0.0.0}}}"
PORT="${2:-${PORT:-${SERVER_PORT:-8088}}}"
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

# Keep repeated `source run.sh` safe in interactive shells.
deactivate 2>/dev/null || true

if [ ! -x "${VENV_DIR}/bin/python" ]; then
  if [ -x "${PROJECT_DIR}/install.sh" ]; then
    "${PROJECT_DIR}/install.sh"
  else
    mkdir -p "$(dirname "${VENV_DIR}")"
    uv venv --python "${PYTHON_BIN}" "${VENV_DIR}"
    uv pip install --python "${VENV_DIR}/bin/python" --upgrade -r requirements.txt
  fi
fi

# shellcheck disable=SC1091
source "${VENV_DIR}/bin/activate"

if [ -f "${PROJECT_DIR}/.env" ]; then
  set -a
  # shellcheck disable=SC1091
  source "${PROJECT_DIR}/.env"
  set +a
fi

export HF_HUB_DISABLE_TELEMETRY="${HF_HUB_DISABLE_TELEMETRY:-1}"
export UV_LINK_MODE="${UV_LINK_MODE:-copy}"
export HOST PORT SERVER_NAME="${HOST}" SERVER_PORT="${PORT}"

if [ -z "${API_TOKEN:-${ENGINE_API_KEY:-}}" ]; then
  echo "API_TOKEN (or legacy ENGINE_API_KEY) must be set in .env or the environment" >&2
  return 1 2>/dev/null || exit 1
fi

if [[ "${BASH_SOURCE[0]}" != "$0" ]]; then
  python -m uvicorn app:app --host "${HOST}" --port "${PORT}"
else
  exec python -m uvicorn app:app --host "${HOST}" --port "${PORT}"
fi
