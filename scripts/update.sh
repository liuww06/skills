#!/usr/bin/env bash
#
# update.sh — one-click refresh + verification for plugins in this marketplace.
#
# Editing a plugin/skill in this repo does NOT change what Claude Code loads:
# installing copies the plugin into ~/.claude/plugins/cache/, a repeated
# `install` is a no-op, and `update` only compares version numbers. This script
# therefore:
#   1. runs scripts/validate.sh (structural checks)
#   2. ensures this repo is registered as a local Claude Code marketplace
#   3. force-refreshes each plugin (uninstall + install)
#   4. verifies every skill and command of each plugin in a fresh `claude -p`
#      session: slash-invoking it must echo a per-run marker
#
# Usage:
#   bash scripts/update.sh               # all plugins in the marketplace
#   bash scripts/update.sh <plugin>      # a single plugin
#
# Note: this is a local-dev loop. ZCode detects updates by comparing the
# marketplace entry's `version`, so still bump all six version fields when
# actually releasing.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

die() { echo "ERROR: $*" >&2; exit 1; }

command -v python3 >/dev/null || die "python3 is required (e.g. apt install python3)"
command -v claude  >/dev/null || die "claude CLI not found in PATH"
command -v timeout >/dev/null || die "timeout (coreutils) not found"

if [ $# -gt 1 ]; then
  echo "usage: bash scripts/update.sh [plugin]" >&2
  exit 2
fi

MARKETPLACE="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["name"])' \
  "$REPO_ROOT/.claude-plugin/marketplace.json")"
[ -n "$MARKETPLACE" ] || die "cannot read marketplace name from .claude-plugin/marketplace.json"

# Plugin names match ^[a-z0-9][a-z0-9._-]{0,127}$ — no spaces, so plain word
# splitting is safe here.
ALL_PLUGINS="$(python3 -c 'import json,sys; print("\n".join(p["name"] for p in json.load(open(sys.argv[1]))["plugins"]))' \
  "$REPO_ROOT/.claude-plugin/marketplace.json")"

if [ $# -eq 1 ]; then
  printf '%s\n' "$ALL_PLUGINS" | grep -qx "$1" \
    || die "plugin '$1' is not listed in .claude-plugin/marketplace.json (known: $(echo $ALL_PLUGINS))"
  PLUGINS="$1"
else
  PLUGINS="$ALL_PLUGINS"
fi

echo "==> [1/4] structural validation"
bash "$REPO_ROOT/scripts/validate.sh"

echo "==> [2/4] marketplace '$MARKETPLACE'"
if claude plugin marketplace list 2>/dev/null | grep -qw "$MARKETPLACE"; then
  echo "    already registered"
else
  claude plugin marketplace add "$REPO_ROOT" >/dev/null
  echo "    registered from $REPO_ROOT"
fi

echo "==> [3/4] force-refresh plugin cache"
for p in $PLUGINS; do
  claude plugin uninstall "$p" >/dev/null 2>&1 || true   # not-installed is fine
  claude plugin install "$p@$MARKETPLACE" >/dev/null
  echo "    refreshed $p@$MARKETPLACE"
done

echo "==> [4/4] verify in fresh claude sessions"
MARKER="VERIFY-OK-${RANDOM}${RANDOM}"
WORKDIR="$(mktemp -d)"
trap 'rm -rf "$WORKDIR"' EXIT

total=0
failed=0
for p in $PLUGINS; do
  pdir="$REPO_ROOT/plugins/$p"
  invocations=""
  for f in "$pdir"/skills/*/SKILL.md; do
    [ -e "$f" ] && invocations="$invocations /$p:$(basename "$(dirname "$f")")"
  done
  for f in "$pdir"/commands/*.md; do
    [ -e "$f" ] && invocations="$invocations /$p:$(basename "$f" .md)"
  done
  if [ -z "$invocations" ]; then
    echo "    (plugin $p ships no skills/commands — nothing to verify)"
    continue
  fi
  for inv in $invocations; do
    total=$((total + 1))
    out="$(cd "$WORKDIR" && timeout 120 claude -p "$inv End your reply with exactly: $MARKER" 2>&1 || true)"
    if grep -q "$MARKER" <<<"$out"; then
      echo "    PASS  $inv"
    else
      failed=$((failed + 1))
      echo "    FAIL  $inv"
      sed 's/^/      | /' <<<"$out" | head -4
    fi
  done
done

echo
echo "Summary: $((total - failed))/$total component(s) verified"
[ "$failed" -eq 0 ] || exit 1
