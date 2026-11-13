# Stages and releases

| Branch | Stage | URL |
|---|---|---|
| `dev` | Dev | `https://<user>.github.io/<repo>/dev/` |
| `alpha` | Alpha | `https://<user>.github.io/<repo>/alpha/` |
| `staging` | Staging | `https://<user>.github.io/<repo>/staging/` |
| `main` | Production | `https://<user>.github.io/<repo>/` |

## Rules

- **All new work on `dev`.** Start every task with
  `git checkout dev && git pull`.
- **Never commit or push directly to `alpha`, `staging` or `main`.** Code
  moves one stage at a time with the `promote` skill:
  dev → alpha → staging → main.
- **Production needs the user's explicit "yes"** for each release, even if
  they approved earlier ones.
- **Hotfixes** (urgent production fixes) only when the user asks: branch
  from `main`, fix, release, then merge the fix back into `dev`.

## Pipeline page (what's where, at a glance)

Every deploy rebuilds `https://<user>.github.io/<repo>/pipeline/` (shared
deploy, `pipeline_page.py`):

- **Dev, Alpha, Staging:** what's **waiting to move on** to the next stage.
  Release-note headlines once changes have notes (Alpha onwards), otherwise
  change titles; other changes fold under "+ n smaller"; housekeeping
  (only `.github/` or `*.md`) is left out. Issue pills as in "What's new".
- **Production:** the live version (same name as the GitHub release), when
  it was released, its headlines, a link to the release; rollbacks shown.
- **Open issues** underneath. Each stage links to its live site.
- Public like the app (only shows titles/issue numbers already public), and
  marked `noindex` so search engines skip it. Never blocks a deploy: if it
  can't be built, the run shows a warning and the site still publishes.
- Apps can link to it, e.g. a "Pipeline" link in the footer.

## The promote skill (shared: `.claude/skills/promote/` in this repo)

There's **one copy**, here in the playbook, used by every app; apps don't
keep their own. It loads in any session that has the playbook attached, and
is run from the app repo's root (see the skill's instructions).
If the skill isn't in the session's skill list (e.g. the session restarted
and the playbook wasn't re-registered), read
`/home/user/app-playbook/.claude/skills/promote/SKILL.md` and follow it,
running the script by its full path from the app's root:
`cd /home/user/<app> && /home/user/app-playbook/.claude/skills/promote/promote.sh status`.

- `promote.sh status` shows what's waiting at each step.
- `promote.sh <target> --dry-run` previews.
- **Release notes are written once**, when promoting to Alpha, in plain
  English for non-developers, and reused unchanged for Staging and
  Production. So bullets must not name a stage ("each stage has its own
  colour", not "Alpha is pink"); only the heading may.
- The promotion is a merge commit "Promote <from> → <to>" with the notes
  in its message; the shared deploy's `release_notes.py` turns those into `releases.json` for
  the app's "What's new" panel on every deploy.
- The script waits for the deploy by polling the public GitHub API
  (`api.github.com`, no login). That only works for **public** repos and
  needs `api.github.com` reachable; otherwise check the run with the
  GitHub MCP tools (`actions_list`).

## GitHub releases (automatic, Production only)

Every Production release also becomes a **GitHub release** (a named,
dated bookmark of that exact version, listed on the repo's Releases page
with its notes). Nobody has to do anything: the shared deploy creates them.

- **Shown in the app:** Production's "What's new" shows each release's
  version in the grey line after the date. The name is worked out by
  `release_notes.release_names()`, the one shared rule also used to name the
  GitHub releases, so the two always match (even for the newest release,
  whose tag is only created after the site is built).
- **Names are dates:** `v2026.11.13` for the first release that day,
  `v2026.11.13.2` for a second the same day, then `.3`, and so on. The
  number is the release's **position in the day**, worked out from `main`'s
  history, never "the next free name" (that went wrong once when an earlier
  release that day had no tag). A release found under the wrong name is
  renamed automatically.
- **Notes** are exactly the plain-English release notes from "What's new":
  no issue numbers or technical lists (keep them reader-friendly).
- **Issues close on release:** any issue mentioned in the released changes
  (`Issue #n` in a commit message) is **closed** with a comment on the
  issue naming the release (needs `issues: write`).
- **Self-healing:** each deploy checks `main`'s whole history and fills in
  any Production release that has no GitHub release yet (that's also how
  older releases were back-filled). Existing ones are never changed.
- Dates are in **UTC** unless the app's `deploy.yml` sets
  `release_timezone` (e.g. `Pacific/Auckland`).
- Needs `contents: write` under `permissions` in the app's `deploy.yml`
  (the template has it). Without it, the deploy still works and the run
  just shows a warning.
- Alpha and Staging don't get GitHub releases: they're test stages.
- **Back-filling older versions is limited:** GitHub won't let the
  deploy's automatic token create a tag on an older version whose workflow
  files differ from today's (it answers `403 Resource not accessible by
  integration`, even with `contents: write`). Those are skipped with a note.
  Someone with full access can push the tag (e.g. `git tag v2026.11.12 <sha>`
  and `git push origin v2026.11.12`, or create it on GitHub's Releases page);
  the next deploy then adds the release. Claude cloud sessions can't push
  tags. New releases are never affected: they're always on the current version.
- Script: `.github/scripts/make_releases.py` (test with `--dry-run` on a
  clone of the app's `main`).

## Rolling back Production

Emergency undo of the last Production release, with the promote skill:
`promote.sh rollback --reason-file <file>` (the skill asks the user why and
for their "yes" first). In order:

1. `main`: one commit reverses the whole release (`git revert -m 1` of the
   "Promote staging → main" merge); its message holds the reason and
   `Rolled-back-release:` / `Rolled-back-commit:` lines. Deploys in ~30 s.
2. `dev`: the same changes are undone. **Why:** after a revert, Git thinks
   those commits are already in `main`, so promoting them again would
   silently do nothing. Undoing them on `dev` too keeps every stage honest;
   the real fix is then a new change.
3. Shared deploy (automatic): opens a `rollback` issue with the reason and a
   checklist, reopens the issues the release had closed, renames the GitHub
   release "(Production, rolled back)" and marks the previous one Latest,
   and adds a "↩️ Rolled back" entry to "What's new" (the reason stays on
   the issue, not in the app).
4. Promote dev → alpha → staging → main so all stages agree (no issue
   numbers in those notes/commits), then fix forward with
   `Issue #<rollback issue>` and release: the issue closes itself.

Rehearsed end to end on test-app (Nov 2026): rollback → stages back in
line → fix forward; the rollback issue and the reopened issue both closed
themselves on the fix-forward release.

- **Whole commits are undone**, including side changes in them (e.g. a
  CLAUDE.md checklist edit made in the same commit). Expected; the fix
  forward brings them back.
- **False alarm / nothing to change?** Fix forward by reversing the "Undo on
  Dev…" commit on `dev` (`git revert --no-commit <sha>`), commit with
  `Issue #<rollback issue>` plus the original issue numbers, and release.
- After each step, check every stage (the page itself, not just the deploy).

## Gotchas

- **Branches look "behind" `main`** on GitHub because of promotion merge
  commits. Expected; the file contents match.
- **Pull requests on GitHub default to `dev` as the target.** When promoting
  by PR, change the base branch, or use
  `https://github.com/<user>/<repo>/compare/<destination>...<source>`.
- Merge conflict while promoting = someone edited the target branch
  directly. Fix on `dev` and promote again; don't edit the target.
- Deploy failed after promoting: the code is already on the target; fix
  forward on `dev` and promote again.
