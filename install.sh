#!/usr/bin/env bash
set -euo pipefail

# Install one or more bundled skills.
#
# Usage:
#   ./install.sh [dest-root] [skill...]
#
# Examples:
#   ./install.sh                                   # all skills -> .agents/skills
#   ./install.sh /path/to/project/.agents/skills   # all skills -> custom root
#   ./install.sh .agents/skills seo-mentor         # only the seo-mentor skill

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEST_ROOT="${1:-.agents/skills}"
shift || true

SKILLS=("$@")
if [ ${#SKILLS[@]} -eq 0 ]; then
  while IFS= read -r dir; do
    SKILLS+=("$(basename "$dir")")
  done < <(find "$REPO_ROOT/skills" -mindepth 1 -maxdepth 1 -type d | sort)
fi

for skill in "${SKILLS[@]}"; do
  SOURCE="$REPO_ROOT/skills/$skill"
  TARGET="$DEST_ROOT/$skill"

  if [ ! -d "$SOURCE" ]; then
    echo "Unknown skill: $skill (expected $SOURCE)" >&2
    exit 1
  fi

  if [ -e "$TARGET" ]; then
    echo "$TARGET already exists" >&2
    exit 1
  fi

  mkdir -p "$(dirname "$TARGET")"
  cp -R "$SOURCE" "$TARGET"
  echo "Installed $skill to $TARGET"
done

echo
echo "Next steps:"
echo "  FMP: node $DEST_ROOT/fmp-guardian/scripts/fmp-init.mjs"
echo "  SEO: see $DEST_ROOT/seo-mentor/SKILL.md"
