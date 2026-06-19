#!/usr/bin/env bash
set -euo pipefail

FORCE=0
if [[ "${1:-}" == "--force" ]]; then
  FORCE=1
fi

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
SKILLS_DIR="$CODEX_HOME/skills"
PROJECT_SKILLS_DIR="$REPO_ROOT/codex_skills"

mkdir -p "$SKILLS_DIR"

echo "Installing project-local Codex skills into: $SKILLS_DIR"

for src in "$PROJECT_SKILLS_DIR"/*; do
  [[ -d "$src" ]] || continue
  name="$(basename "$src")"
  dest="$SKILLS_DIR/$name"
  if [[ -e "$dest" && "$FORCE" != "1" ]]; then
    echo "skip $name (already exists; use --force to overwrite)"
    continue
  fi
  rm -rf "$dest"
  cp -R "$src" "$dest"
  echo "installed $name"
done

INSTALLER="$CODEX_HOME/skills/.system/skill-installer/scripts/install-skill-from-github.py"
if [[ -f "$INSTALLER" ]]; then
  if [[ ! -d "$SKILLS_DIR/gen-pseudocode-skill" && ! -d "$SKILLS_DIR/algo-reconstruct" ]]; then
    echo "Attempting to install external pseudocode skill from HuiyuLi-2000/gen-pseudocode-skill"
    python3 "$INSTALLER" --repo HuiyuLi-2000/gen-pseudocode-skill --path . --name gen-pseudocode-skill || {
      echo "warning: skill-installer failed; trying git clone fallback"
      tmp_dir="$(mktemp -d)"
      if git clone --depth 1 https://github.com/HuiyuLi-2000/gen-pseudocode-skill.git "$tmp_dir/gen-pseudocode-skill"; then
        if [[ -f "$tmp_dir/gen-pseudocode-skill/SKILL.md" ]]; then
          rm -rf "$SKILLS_DIR/gen-pseudocode-skill"
          cp -R "$tmp_dir/gen-pseudocode-skill" "$SKILLS_DIR/gen-pseudocode-skill"
          echo "installed gen-pseudocode-skill via git fallback"
        else
          echo "warning: cloned repo does not contain SKILL.md at root"
        fi
      else
        echo "warning: external pseudocode skill install failed; install it manually if needed"
      fi
      rm -rf "$tmp_dir"
    }
  else
    echo "skip external pseudocode skill (already installed)"
  fi
else
  echo "warning: Codex skill-installer not found at $INSTALLER"
  echo "manual install: python3 <skill-installer>/install-skill-from-github.py --repo HuiyuLi-2000/gen-pseudocode-skill --path ."
fi

echo "Done. Restart Codex to pick up new skills."
