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

## The promote skill (`templates/.claude/skills/promote/`)

- `promote.sh status` shows what's waiting at each step.
- `promote.sh <target> --dry-run` previews.
- **Release notes are written once**, when promoting to Alpha, in plain
  English for non-developers, and reused unchanged for Staging and
  Production. So bullets must not name a stage ("each stage has its own
  colour", not "Alpha is pink"); only the heading may.
- The promotion is a merge commit "Promote <from> → <to>" with the notes
  in its message; `release_notes.py` turns those into `releases.json` for
  the app's "What's new" panel on every deploy.
- The script waits for the deploy by polling the public GitHub API
  (`api.github.com`, no login). That only works for **public** repos and
  needs `api.github.com` reachable; otherwise check the run with the
  GitHub MCP tools (`actions_list`).

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
