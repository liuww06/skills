#!/usr/bin/env bash
# Refresh and inspect discovery; task behavior is evaluated separately.
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
exec python3 "$REPO_ROOT/scripts/update.py" "$@"
