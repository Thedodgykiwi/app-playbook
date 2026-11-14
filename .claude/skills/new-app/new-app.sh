#!/usr/bin/env bash
# Set up an empty (or README-only) GitHub repo as a new app from the starter.
#   new-app.sh --name "My App" --short "My" --description "One line" [--dry-run]
# Run from the NEW repo's root. It:
#   1. copies templates/starter (app skeleton, sign-in module dormant), the
#      small deploy.yml and the CLAUDE.md template, filling in the app's
#      name, description, owner and repo;
#   2. commits on main and pushes it;
#   3. creates dev, alpha and staging from main and pushes them;
#   4. reports the first deploy and checks the shared issue labels appeared.
# The three GitHub settings (Pages source, deployment branches, default
# branch) can't be done from here: the skill walks the user through them.
set -euo pipefail

die() { echo "ERROR: $*" >&2; exit 1; }
HERE="$(cd "$(dirname "$0")" && pwd)"
PLAYBOOK="$(cd "$HERE/../../.." && pwd)"
TPL="$PLAYBOOK/templates"

name= short= desc= dry=false
while (( $# )); do
  case $1 in
    --name) name=${2:?}; shift ;;
    --short) short=${2:?}; shift ;;
    --description) desc=${2:?}; shift ;;
    --dry-run) dry=true ;;
    *) die "Unknown option '$1'" ;;
  esac
  shift
done
[[ -n $name ]] || die "Pass --name \"App name\"."
[[ -n $short ]] || short=$name
[[ -n $desc ]] || desc="A new app."
[[ $name != *'#'* && $short != *'#'* ]] || die "Names can't contain '#'."

cd "$(git rev-parse --show-toplevel 2>/dev/null)" || die "Run this from inside the new app's git repo."
[[ $(pwd) != "$PLAYBOOK" ]] || die "This is the playbook itself; run it from the new app's repo."
# The address as configured (not after any url.*.insteadOf rewriting).
remote=$(git config --get remote.origin.url) || die "No 'origin' remote."
slug=$(sed -E 's#(\.git)?$##; s#^.*github\.com[:/]##' <<<"$remote")
owner=${slug%%/*}; repo=${slug#*/}; owner_lc=$(tr '[:upper:]' '[:lower:]' <<<"$owner")
[[ $slug == */* ]] || die "Couldn't read owner/repo from '$remote'."

git fetch -q origin 2>/dev/null || true
for b in dev alpha staging; do
  git ls-remote --exit-code --heads origin "$b" >/dev/null 2>&1 && die "Branch '$b' already exists: this repo looks set up already."
done
[[ -z $(git status --porcelain) ]] || die "Uncommitted changes; commit or remove them first."
existing=$(git ls-files | grep -vE '^(README\.md|LICENSE(\..*)?|\.gitignore)$' || true)
[[ -z $existing ]] || die "The repo already has files besides README/LICENSE/.gitignore:
$existing
Use an empty repo, so nothing gets overwritten."

echo "Setting up '$name' in $slug"
echo "  Stages: https://$owner_lc.github.io/$repo/ (+ /dev/, /alpha/, /staging/, /pipeline/)"
$dry && { echo "(dry run: nothing changed)"; exit 0; }

# 1. main with the starter, on top of whatever the repo already has (e.g. its README)
git ls-remote origin >/dev/null 2>&1 || die "Can't reach the repo on GitHub ($slug). Check it exists and is attached to this session."
default=$(git ls-remote --symref origin HEAD 2>/dev/null | sed -nE 's#^ref: refs/heads/([^[:space:]]+)[[:space:]]+HEAD#\1#p' || true)
base=
for b in "$default" main master; do
  [[ -n $b ]] && git rev-parse -q --verify "origin/$b" >/dev/null && { base="origin/$b"; break; }
done
if [[ -n $base ]]; then
  git checkout -q -B main "$base"
else
  git checkout -q --orphan main 2>/dev/null || git checkout -q -B main   # truly empty repo
fi
# If anything below fails before the push, put the working tree back so a re-run works.
trap 'if ! git ls-remote --exit-code --heads origin dev >/dev/null 2>&1; then git reset -q --hard 2>/dev/null; git clean -qfd 2>/dev/null; fi' EXIT
cp -R "$TPL/starter/." .
mkdir -p .github/workflows
cp "$TPL/.github/workflows/deploy.yml" .github/workflows/deploy.yml
cp "$TPL/CLAUDE.md.template" CLAUDE.md

NAME="$name" SHORT="$short" DESC="$desc" OWNER_LC="$owner_lc" REPO="$repo" python3 - <<'PY'
import os, pathlib, re
v = {k: os.environ[k] for k in ("NAME", "SHORT", "DESC", "OWNER_LC", "REPO")}
skip = {".png", ".jpg", ".ico", ".gif", ".webp"}
for p in pathlib.Path(".").rglob("*"):
    if not p.is_file() or ".git" in p.parts or p.suffix in skip:
        continue
    try:
        s = p.read_text(encoding="utf-8")
    except UnicodeDecodeError:   # binary file the repo already had (zip, font…): leave it alone
        continue
    t = (s.replace("{{APP_NAME}}", v["NAME"]).replace("{{SHORT_NAME}}", v["SHORT"]).replace("{{DESCRIPTION}}", v["DESC"])
          .replace("{{OWNER_LC}}", v["OWNER_LC"]).replace("{{REPO}}", v["REPO"]))
    if p.name == "CLAUDE.md":
        t = (t.replace("# <app-name>", "# " + v["NAME"], 1)
              .replace("<One or two sentences: what the app does and who it's for.>", v["DESC"])
              .replace("<user>", v["OWNER_LC"]).replace("<repo>", v["REPO"])
              .replace("<list the app's key features here>", "the page loads without errors"))
    if p.as_posix() == ".github/workflows/deploy.yml":
        t = re.sub(r"app_name: .*", f'app_name: {v["NAME"]}', t)
        t = re.sub(r"short_name: .*", f'short_name: {v["SHORT"]}', t)
    if t != s:
        p.write_text(t, encoding="utf-8")
PY
grep -rl '{{' --include='*.html' --include='*.js' --include='*.md' --include='*.webmanifest' . 2>/dev/null | grep -v '^./.git/' && die "Some placeholders weren't filled in (see above)."

git add -A
git commit -q -m "Set up $name from the app starter

Blank starting page (an empty placeholder box) with dormant Google
sign-in, the small deploy.yml that calls the shared playbook
deploy, and CLAUDE.md from the playbook template.

Co-Authored-By: Claude <noreply@anthropic.com>"
git push -q -u origin main 2>&1 | grep -v '^remote:' || true
[[ $(git ls-remote origin refs/heads/main | cut -f1) == $(git rev-parse HEAD) ]] || die "Push to main failed."
echo "Pushed main."

# 2. stage branches (dev last, so it's the one the first deploy runs for)
for b in staging alpha dev; do
  git push -q origin "main:refs/heads/$b" 2>&1 | grep -v '^remote:' || true
  git ls-remote --exit-code --heads origin "$b" >/dev/null || die "Couldn't create branch '$b'."
  echo "Created $b."
done
# dev is the same commit as main. Don't rely on origin/dev: a single-branch
# (shallow) clone, as cloud sessions make, doesn't fetch other branches.
git config --get-all remote.origin.fetch | grep -qF 'refs/heads/*' || git config --add remote.origin.fetch '+refs/heads/*:refs/remotes/origin/*'
git fetch -q origin 2>/dev/null || true
git checkout -q -B dev main && git branch -q --set-upstream-to=origin/dev dev 2>/dev/null || true

# 3. first deploy + labels (public repos: the API needs no login)
api="https://api.github.com/repos/$slug"
echo "Waiting for the first deploy run…"
for _ in $(seq 1 30); do
  sleep 10
  read -r status conclusion < <(curl -fsS "$api/actions/runs?branch=dev&per_page=1" 2>/dev/null | python3 -c '
import json, sys
r = (json.load(sys.stdin).get("workflow_runs") or [{}])[0]
print(r.get("status", "none"), r.get("conclusion") or "-")' 2>/dev/null || echo "unreachable -")
  [[ $status == completed ]] && break
done
echo "First deploy: ${status:-unknown} / ${conclusion:-unknown} (expected to fail until GitHub Pages is switched on)."
labels=$(curl -fsS "$api/labels?per_page=100" 2>/dev/null | python3 -c 'import json,sys;print(" ".join(l["name"] for l in json.load(sys.stdin)))' 2>/dev/null || echo "")
for l in bug feature tweak performance rollback; do
  [[ " $labels " == *" $l "* ]] && echo "  label ok: $l" || echo "  label missing: $l (appears after the next successful deploy)"
done
echo
echo "Done. Next: the three GitHub settings (see the skill), then re-run the deploy."
