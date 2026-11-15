# Upgrading an existing app to the current starter

Each app owns its copy of the starter (`templates/starter/`) and of
`CLAUDE.md` from the template, so improvements made later **don't reach it on
their own**. (Shared parts, like the deploy, promote skill, labels and pipeline
page, update everywhere automatically: `README.md`, "Shared by every app".)
This guide brings an app up to date, one small piece at a time.

## When

- The session catch-up notices the app is behind (below), or
- the user asks ("bring this app up to date", "does it have the latest
  starter?"), or
- you're about to build something the starter now provides (offline mode,
  settings, error screen…): upgrade that piece instead of building it again.

Never upgrade silently during an unrelated task: offer it.

## How far behind is it?

- `docs/starter-version.md` in the app records the playbook commit it was
  set up from (written by `new-app`; apps older than Nov 2026 don't have it:
  treat them as "before the brief").
- Compare: `git -C /home/user/app-playbook log --oneline <that-commit>..main
  -- templates/starter templates/CLAUDE.md.template` lists what changed in
  the starter and template since then. No commit recorded → compare file by
  file (`diff -r`) against `templates/starter/`, ignoring the app's own code.

## Steps

1. **List the differences in plain English**, grouped as features the user
   would notice (e.g. "works offline", "text size setting", "friendly error
   screen", "the brief") and behind-the-scenes ones (CLAUDE.md sections,
   checks). Skip anything the app replaced on purpose (check its CLAUDE.md
   and history).
2. **Show the list with a choice card** (AskUserQuestion, multi-select):
   which to bring in now; the rest can be logged.
3. **Each chosen piece = one `tweak` (or `feature`) issue**, done like any
   change on `dev`: copy from the starter, adapt to the app's own code (the
   app's files may have changed; merge by hand, don't overwrite), run the
   checks (`testing-and-testers.md`), screenshot.
4. **CLAUDE.md:** add missing template sections (e.g. "Before anything
   else", "Brief", "Checks") without losing the app's own notes.
5. Missing **brief** → draft it (`new-app-kickoff.md` §6).
6. Update `docs/starter-version.md` to the playbook commit you compared
   against, listing what was brought in and what was left out on purpose.

## Keep it easy for next time

When you improve `templates/starter/` or the CLAUDE.md template, write the
commit message so it reads as an upgrade note ("Starter: friendly error
screen when start-up fails"), since that's what step 1 reads.
