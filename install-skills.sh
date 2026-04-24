#!/usr/bin/env bash
# install-skills.sh — installs the sdlc-skills-library skill library into Claude Code

set -e

SCRIPT_NAME="$(basename "$0")"
SKILLS_ROOT="$(cd "$(dirname "$0")/skills" && pwd)"

print_help() {
  local skill_count
  skill_count=$(find "$SKILLS_ROOT" -name "SKILL.md" | wc -l | tr -d ' ')

  cat <<EOF
sdlc-skills-library skill installer
========================

Installs the sdlc-skills-library skill library (${skill_count} skills across 4 phases + 1 workflow
orchestrator) into Claude Code so skills become available on demand.

USAGE
  $SCRIPT_NAME [OPTIONS] [PROJECT_PATH]

OPTIONS
  -h, --help       Show this help and exit.
  --copy           Copy files instead of symlinking. Standalone snapshot that
                   is NOT updated when the sdlc-skills-library repo changes. Best for
                   team members who just consume the library.
  --dry-run        Show what would be installed without writing anything.
  --force          Overwrite existing skill directories without prompting.
                   By default, existing directories are skipped.

ARGUMENTS
  PROJECT_PATH     Optional. If provided, install to PROJECT_PATH/.claude/skills/.
                   If omitted, install globally to ~/.claude/skills/.

INSTALL MODES
  Symlink (default)
    Each installed skill is a symlink into this repo. Edits to the repo are
    reflected everywhere immediately. Symlinks break if this repo moves.
    Best when you are actively developing skills.

  Copy (--copy)
    Each installed skill is a full copy. No updates unless you re-run the
    installer. Portable across machines — can be committed into a project.

EXAMPLES
  $SCRIPT_NAME                                 Install globally (symlinks)
  $SCRIPT_NAME --copy                          Install globally (copies)
  $SCRIPT_NAME ~/Projects/myapp                Install into a project (symlinks)
  $SCRIPT_NAME ~/Projects/myapp --copy         Install into a project (copies)
  $SCRIPT_NAME --dry-run                       Preview without installing
  $SCRIPT_NAME --force                         Overwrite existing installations

AFTER INSTALLATION
  Global install
    Skills are active in every Claude Code session.
    Verify: ls ~/.claude/skills/

  Project install
    Skills are active when Claude Code opens that project.
    - With --copy: commit .claude/skills/ (portable snapshot, survives across machines).
    - Without --copy: add .claude/skills/ to .gitignore (symlinks are machine-specific).

REFERENCE
  skills/INDEX.md        Full skill list with one-line descriptions
  skills/MASTER-GUIDE.md When to use each skill
  docs/quickstart.md     Where to start for a given situation
  docs/modes.md          Operating modes (Nano / Lean / Standard / Rigorous)
  docs/skill-triggers.md Natural-language phrases that activate each skill

EOF
}

# --- argument parsing -------------------------------------------------------

TARGET_PROJECT=""
USE_COPY=false
DRY_RUN=false
FORCE=false

while [ $# -gt 0 ]; do
  case "$1" in
    -h|--help)
      print_help
      exit 0
      ;;
    --copy)
      USE_COPY=true
      ;;
    --dry-run)
      DRY_RUN=true
      ;;
    --force)
      FORCE=true
      ;;
    --*)
      echo "error: unknown option '$1'" >&2
      echo "run '$SCRIPT_NAME --help' for usage." >&2
      exit 2
      ;;
    -*)
      echo "error: unknown option '$1'" >&2
      echo "run '$SCRIPT_NAME --help' for usage." >&2
      exit 2
      ;;
    *)
      if [ -n "$TARGET_PROJECT" ]; then
        echo "error: unexpected extra argument '$1' (project path already set to '$TARGET_PROJECT')" >&2
        echo "run '$SCRIPT_NAME --help' for usage." >&2
        exit 2
      fi
      TARGET_PROJECT="$1"
      ;;
  esac
  shift
done

# --- target directory resolution --------------------------------------------

if [ -n "$TARGET_PROJECT" ]; then
  if [ ! -d "$TARGET_PROJECT" ]; then
    echo "error: project path does not exist: $TARGET_PROJECT" >&2
    exit 1
  fi
  INSTALL_DIR="$TARGET_PROJECT/.claude/skills"
  INSTALL_TYPE="project"
else
  INSTALL_DIR="$HOME/.claude/skills"
  INSTALL_TYPE="global"
fi

# --- header -----------------------------------------------------------------

mode_label="symlink"
[ "$USE_COPY" = true ] && mode_label="copy"
[ "$DRY_RUN" = true ]  && mode_label="$mode_label (dry-run)"

echo ""
echo "sdlc-skills-library skill installer"
echo "========================"
echo "Source:  $SKILLS_ROOT"
echo "Target:  $INSTALL_DIR"
echo "Mode:    $mode_label"
echo "Scope:   $INSTALL_TYPE"
[ "$FORCE" = true ] && echo "Force:   yes (existing directories will be overwritten)"
echo ""

if [ "$DRY_RUN" = false ]; then
  mkdir -p "$INSTALL_DIR"
fi

# --- install loop -----------------------------------------------------------

installed=0
skipped=0

while IFS= read -r skill_file; do
  skill_dir="$(dirname "$skill_file")"
  skill_name="$(basename "$skill_dir")"
  dest="$INSTALL_DIR/$skill_name"

  if [ "$DRY_RUN" = true ]; then
    if [ -e "$dest" ] && [ "$FORCE" = false ] && [ ! -L "$dest" ]; then
      echo "  would skip:   $skill_name (directory already exists; use --force to overwrite)"
      ((skipped++)) || true
    elif [ "$USE_COPY" = true ]; then
      echo "  would copy:   $skill_name"
      ((installed++)) || true
    else
      echo "  would link:   $skill_name → $skill_dir"
      ((installed++)) || true
    fi
    continue
  fi

  if [ "$USE_COPY" = true ]; then
    if [ -d "$dest" ] || [ -L "$dest" ]; then
      if [ "$FORCE" = true ] || [ -L "$dest" ]; then
        rm -rf "$dest"
      else
        echo "  skipped: $skill_name (directory already exists — pass --force to overwrite)"
        ((skipped++)) || true
        continue
      fi
    fi
    cp -r "$skill_dir" "$dest"
    echo "  copied:  $skill_name"
  else
    if [ -L "$dest" ]; then
      rm "$dest"
    elif [ -d "$dest" ]; then
      if [ "$FORCE" = true ]; then
        rm -rf "$dest"
      else
        echo "  skipped: $skill_name (directory already exists — pass --force to overwrite)"
        ((skipped++)) || true
        continue
      fi
    fi
    ln -s "$skill_dir" "$dest"
    echo "  linked:  $skill_name → $skill_dir"
  fi

  ((installed++)) || true
done < <(find "$SKILLS_ROOT" -name "SKILL.md" | sort)

# --- footer -----------------------------------------------------------------

echo ""
if [ "$DRY_RUN" = true ]; then
  echo "Dry run: $installed skill(s) would be installed, $skipped would be skipped."
  echo "Re-run without --dry-run to apply."
else
  echo "Done: $installed skill(s) installed, $skipped skipped."
fi
echo ""

if [ "$DRY_RUN" = false ]; then
  if [ "$INSTALL_TYPE" = "project" ]; then
    echo "Next steps:"
    if [ "$USE_COPY" = true ]; then
      echo "  - Commit .claude/skills/ (portable snapshot, survives across machines)"
    else
      echo "  - Add .claude/skills/ to .gitignore (symlinks are machine-specific)"
    fi
    echo "  - Open the project in Claude Code — skills are active immediately"
  else
    echo "Skills are now active globally across all your Claude Code projects."
    echo "To verify: ls ~/.claude/skills/"
  fi
  echo ""
fi
