#!/usr/bin/env bash
# Python entrypoint; works from any working directory.
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
exec python3 "$REPO_ROOT/scripts/validate.py" "$@"
