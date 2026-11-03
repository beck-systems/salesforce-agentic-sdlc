#!/usr/bin/env bash
# Install /sf-ticket into ~/.claude (skill, agents, guard hooks).
# Never overwrites an existing config.json or org-profile.md.
set -euo pipefail

SRC="$(cd "$(dirname "$0")" && pwd)"
DEST="${CLAUDE_HOME:-$HOME/.claude}"

mkdir -p "$DEST/skills" "$DEST/agents" "$DEST/hooks"

rsync -a --exclude config.json --exclude references/org-profile.md \
  "$SRC/skill/sf-ticket/" "$DEST/skills/sf-ticket/"
cp "$SRC"/agents/*.md "$DEST/agents/"
cp "$SRC"/hooks/*.py "$DEST/hooks/"
chmod +x "$DEST"/hooks/sf-*-guard.py

SKILL="$DEST/skills/sf-ticket"
[ -f "$SKILL/config.json" ] || cp "$SKILL/config.example.json" "$SKILL/config.json"
[ -f "$SKILL/references/org-profile.md" ] || \
  cp "$SKILL/references/org-profile.example.md" "$SKILL/references/org-profile.md"

echo "Installed /sf-ticket into $DEST"
echo "Next:"
echo "  1. Edit $SKILL/config.json            (cases dir, repo path, org aliases, protected paths)"
echo "  2. Edit $SKILL/references/org-profile.md (Jira, Confluence, Slack, Gearset, conventions)"
echo "  3. Restart Claude Code, then run: /sf-ticket <KEY>"
