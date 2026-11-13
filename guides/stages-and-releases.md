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

- **Names are dates:** `v2026.11.13` for the first release that day,
  `v2026.11.13.2` for a second the same day, then `.3`, and so on.
- **Notes** are the same plain-English release notes as "What's new".
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
