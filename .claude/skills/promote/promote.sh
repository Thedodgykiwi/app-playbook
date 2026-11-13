#!/usr/bin/env bash
# Promote one stage to the next and wait for its GitHub Pages deploy.
#   promote.sh status               show commits waiting at each step
#   promote.sh <target> [--dry-run] [--notes-file FILE] [--intro-file FILE]
#       Promote the previous stage into <target>.
#       --notes-file  release notes to use (required for alpha: dev has none)
#       --intro-file  optional extra paragraph placed above reused notes
#   Past alpha, notes are reused automatically from the previous stage.
#   promote.sh rollback --reason-file FILE [--dry-run]
#       Emergency undo of the last Production release: reverses it on main
#       (reason recorded in the commit), waits for the deploy, then undoes
#       the same changes on dev so every stage can be brought back in line.
set -euo pipefail

STAGES=(dev alpha staging main)
REMOTE=origin

die() { echo "ERROR: $*" >&2; exit 1; }

cd "$(git rev-parse --show-toplevel)"

repo_slug() {
  git remote get-url "$REMOTE" | sed -E 's#(\.git)?$##; s#^.*github\.com[:/]##'
}

previous_stage() {
  local target=$1 i
  for i in "${!STAGES[@]}"; do
    if [[ ${STAGES[$i]} == "$target" ]]; then
      (( i == 0 )) && die "'dev' is the first stage; nothing promotes into it."
      echo "${STAGES[$((i-1))]}"; return
    fi
  done
  die "Unknown stage '$target'. Use one of: ${STAGES[*]:1} (production = main)."
}

stage_url() {
  local slug owner repo
  slug=$(repo_slug); owner=${slug%%/*}; repo=${slug#*/}
  owner=$(echo "$owner" | tr '[:upper:]' '[:lower:]')
  if [[ $1 == main ]]; then echo "https://$owner.github.io/$repo/"
  else echo "https://$owner.github.io/$repo/$1/"; fi
}

pending() {  # commits in $1 not yet in $2 (ignoring promotion merge commits)
  git log --no-merges --format='  %h %s (%an)' "$REMOTE/$2..$REMOTE/$1"
}

git fetch -q "$REMOTE" "${STAGES[@]}"

wait_for_deploy() {  # branch sha -> returns when the deploy for that commit succeeded
  local branch=$1 sha=$2 api status conclusion url
  api="https://api.github.com/repos/$(repo_slug)/actions/runs?branch=$branch&head_sha=$sha&per_page=1"
  for _ in $(seq 1 36); do  # up to ~6 minutes
    sleep 10
    read -r status conclusion url < <(curl -fsS "$api" 2>/dev/null | python3 -c '
import json, sys
runs = json.load(sys.stdin).get("workflow_runs", [])
r = runs[0] if runs else {}
print(r.get("status", "none"), r.get("conclusion") or "-", r.get("html_url", "-"))' 2>/dev/null || echo "unreachable - -")
    if [[ $status == completed ]]; then
      [[ $conclusion == success ]] && { echo "Deploy succeeded: $(stage_url "$branch")"; return 0; }
      die "Deploy finished with '$conclusion': $url"
    fi
  done
  die "Timed out waiting for the deploy. Check the Actions tab on GitHub."
}

push_branch() {  # branch -> push HEAD and check it landed
  local branch=$1 sha; sha=$(git rev-parse HEAD)
  git push -q "$REMOTE" "$branch" 2>&1 | grep -v '^remote:' || true
  [[ $(git ls-remote "$REMOTE" "refs/heads/$branch" | cut -f1) == "$sha" ]] || die "Push to $branch failed."
  echo "Pushed $branch at ${sha:0:7}. Waiting for deploy…"
}

rollback() {
  local reason_file= dry_run=false
  while (( $# )); do
    case $1 in
      --dry-run) dry_run=true ;;
      --reason-file) reason_file=${2:?--reason-file needs a path}; shift ;;
      *) die "Unknown option '$1'" ;;
    esac
    shift
  done
  [[ -s $reason_file || $dry_run == true ]] || die "Say why: pass --reason-file with the reason for the rollback."
  git fetch -q --tags "$REMOTE"

  # Releases already rolled back (recorded in earlier rollback commits).
  local undone; undone=$(git log --first-parent --format=%B "$REMOTE/main" | sed -n 's/^Rolled-back-commit: //p')
  # Newest Production release (promotion or PR merge into main) not yet rolled back.
  local last= c
  for c in $(git rev-list --first-parent --merges "$REMOTE/main"); do
    grep -qx "$c" <<<"$undone" && continue
    last=$c; break
  done
  [[ -n $last ]] || die "No Production release found to roll back."
  local tag prev prevtag
  tag=$(git tag --points-at "$last" --list 'v[0-9]*' | head -1)
  prev=$(git rev-list --first-parent --merges "$last^1" | while read -r c; do grep -qx "$c" <<<"$undone" || { echo "$c"; break; }; done)
  prevtag=${prev:+$(git tag --points-at "$prev" --list 'v[0-9]*' | head -1)}
  local changes; changes=$(git log --no-merges --reverse --format='%H %s' "$last^1..$last")
  echo "Live now:      ${tag:-release ${last:0:7}} ($(git log -1 --format=%cs "$last"))"
  echo "Going back to: ${prevtag:-the version before it}${prev:+ (${prev:0:7})}"
  echo "Changes that will be undone:"; sed 's/^[0-9a-f]* /  - /' <<<"$changes"
  $dry_run && { echo "(dry run: nothing changed)"; exit 0; }

  [[ -z $(git status --porcelain) ]] || die "Working tree has uncommitted changes; commit or stash them first."
  local start_branch; start_branch=$(git branch --show-current)
  trap 'git checkout -q "$start_branch" 2>/dev/null || true' EXIT

  # 1. Production: reverse the whole release in one commit.
  git checkout -q -B main "$REMOTE/main"
  git revert -m 1 --no-commit "$last" || { git revert --abort; die "Couldn't reverse ${last:0:7} cleanly."; }
  local msg; msg=$(mktemp)
  {
    echo "Roll back Production: undo ${tag:-${last:0:7}}"
    echo
    echo "Reason:"; cat "$reason_file"; echo
    echo "Changes undone:"; sed 's/^[0-9a-f]* /  - /' <<<"$changes"
    echo
    echo "Rolled-back-release: ${tag:-none}"
    echo "Rolled-back-commit: $last"
  } > "$msg"
  git commit -q -F "$msg"
  push_branch main; wait_for_deploy main "$(git rev-parse HEAD)"

  # 2. Dev: undo the same changes, so later promotions can't bring them back
  #    by accident (and so the fix can be made on top of a working Dev).
  #    The message deliberately has no "#" numbers: it mustn't close issues.
  git checkout -q -B dev "$REMOTE/dev"
  local shas; shas=$(cut -d' ' -f1 <<<"$changes" | tac)
  if ! git revert --no-commit $shas; then
    git revert --abort
    echo "⚠️  Production is rolled back, but undoing the same changes on dev hit a conflict."
    echo "   Undo them on dev by hand (oldest last): $(tr '\n' ' ' <<<"$shas")"
    exit 1
  fi
  {
    echo "Undo on Dev what was rolled back in Production (${tag:-${last:0:7}})"
    echo
    echo "Brings Dev back to the working version after the Production rollback,"
    echo "so the change can be fixed and re-released properly. Undoes:"
    sed 's/^[0-9a-f]* /  - /' <<<"$changes"
  } > "$msg"
  git commit -q -F "$msg"
  push_branch dev; wait_for_deploy dev "$(git rev-parse HEAD)"
  echo
  echo "Rolled back. Next: promote dev → alpha → staging → main so every stage agrees;"
  echo "then fix on dev and release as usual."
}

if [[ ${1:-} == rollback ]]; then shift; rollback "$@"; exit 0; fi

if [[ ${1:-} == status || -z ${1:-} ]]; then
  for ((i=0; i<${#STAGES[@]}-1; i++)); do
    src=${STAGES[$i]}; dst=${STAGES[$((i+1))]}
    list=$(pending "$src" "$dst")
    if [[ -n $list ]]; then
      echo "$src → $dst: $(echo "$list" | wc -l) commit(s) waiting"; echo "$list"
    else
      echo "$src → $dst: up to date"
    fi
  done
  exit 0
fi

target=$1; shift; [[ $target == production || $target == prod ]] && target=main
dry_run=false; notes_file=; intro_file=
while (( $# )); do
  case $1 in
    --dry-run) dry_run=true ;;
    --notes-file) notes_file=${2:?--notes-file needs a path}; shift ;;
    --intro-file) intro_file=${2:?--intro-file needs a path}; shift ;;
    *) die "Unknown option '$1'" ;;
  esac
  shift
done
[[ -z $notes_file || -s $notes_file ]] || die "Notes file '$notes_file' is missing or empty."
[[ -z $intro_file || -s $intro_file ]] || die "Intro file '$intro_file' is missing or empty."
source=$(previous_stage "$target")

list=$(pending "$source" "$target")
if [[ -z $list ]] && git merge-base --is-ancestor "$REMOTE/$source" "$REMOTE/$target"; then
  echo "Nothing to promote: $target already has everything from $source."; exit 0
fi
echo "Promoting $source → $target. Commits:"
echo "${list:-  (merge commits only)}"

# Past alpha, reuse the notes already written for these changes.
if [[ -z $notes_file && $target != alpha ]]; then
  notes_file=$(mktemp)
  python3 "$(dirname "$0")/combine_notes.py" "$REMOTE/$target" "$REMOTE/$source" \
    "$target" "$source" ${intro_file:+"$intro_file"} > "$notes_file"
  [[ -s $notes_file ]] || die "No release notes found on $source to reuse; pass --notes-file."
  echo; echo "Release notes (reused from $source):"; echo; cat "$notes_file"; echo
fi
[[ -n $notes_file || $dry_run == true ]] || die "Release notes are required when promoting to alpha: pass --notes-file."
$dry_run && { echo "(dry run: nothing changed)"; exit 0; }

[[ -z $(git status --porcelain) ]] || die "Working tree has uncommitted changes; commit or stash them first."

start_branch=$(git branch --show-current)
trap 'git checkout -q "$start_branch" 2>/dev/null || true' EXIT

git checkout -q -B "$target" "$REMOTE/$target"
msg=$(mktemp)
{
  echo "Promote $source → $target"
  echo
  if [[ -n $notes_file ]]; then
    echo "Release notes:"; cat "$notes_file"; echo
  fi
  echo "Changes included:"
  echo "${list:-  (merge commits only)}"
} > "$msg"
if ! git merge -q --no-ff "$REMOTE/$source" -F "$msg"; then
  conflicts=$(git diff --name-only --diff-filter=U)
  git merge --abort
  die "Merge conflict promoting $source → $target in: $conflicts"
fi
sha=$(git rev-parse HEAD)
git push -q "$REMOTE" "$target" 2>&1 | grep -v '^remote:' || true
[[ $(git ls-remote "$REMOTE" "refs/heads/$target" | cut -f1) == "$sha" ]] || die "Push to $target failed."
echo "Pushed $target at ${sha:0:7}. Waiting for deploy…"

wait_for_deploy "$target" "$sha"
