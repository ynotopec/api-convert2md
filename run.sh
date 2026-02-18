#!/usr/bin/env bash
set -euo pipefail

server_address="${1:-0.0.0.0}"
port_number="${2:-8088}"
python_version="${PYTHON_BIN:-python3}"

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

venv_dir="${VENV_DIR:-$DIR/.venv}"
if [ ! -d "$venv_dir" ]; then
  "$python_version" -m venv "$venv_dir"
fi
# shellcheck disable=SC1091
source "$venv_dir/bin/activate"

"$python_version" -m pip install -U pip setuptools wheel
"$python_version" -m pip install -r requirements.txt

# Load optional local environment file.
if [ -f ".env" ]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

if [ -z "${ENGINE_API_KEY:-}" ]; then
  echo "ENGINE_API_KEY is required (set it in environment or .env)"
  exit 1
fi

exec "$python_version" -m uvicorn app:app --host "$server_address" --port "$port_number"
