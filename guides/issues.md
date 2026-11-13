# Logging issues and requests (GitHub Issues)

Use each app's **GitHub Issues** as its to-do list: bugs, feature requests,
small tweaks and slowness reports, logged as they come in and worked on
later. Claude creates, lists, updates and closes issues with the GitHub
tools (`issue_write`, `list_issues`, `issue_read`, `add_issue_comment`).

## The golden rule: "log it" means record only

When the user says **"log it"** (or "add an issue", "note that down"),
create the issue and **don't change any code**. Work starts only when they
say so ("let's do #12", "fix the slow menu").

## Labels (shared by every app)

Kept once in this repo's `.github/labels.json`; the shared deploy makes sure
every app has them (needs `issues: write` in the app's `deploy.yml`).

| Label | Use for |
|---|---|
| `bug` | Something's broken or not working as it should |
| `feature` | Something new the app should do |
| `tweak` | Small visual or wording change: colour, outline, text |
| `performance` | Something is slow: loading, opening, saving |
| `priority: high` | Do soon: it affects people now |
| `priority: low` | Nice to have, no rush |

One type label per issue; add a priority only if the user gives one (or it's
clearly urgent, e.g. people can't sign in). GitHub's default labels
(`accessibility`, `question`, …) stay available too.

## Writing a good issue

**Title:** short and specific, saying what's wrong or wanted, not the fix.
"Settings menu is slow to open", not "Optimise menu".

**Body:**

```markdown
**What's happening / what's wanted**
<one or two plain sentences>

**Where**
<stage and page, e.g. Production, account menu; device/browser if known>

**Expected**
<what it should do / look like>

**Reported by**
<role, e.g. "client", "tester", "us": never a name, email or private detail>

**Notes**
<anything else: how often, screenshots, ideas, links>
```

Leave out sections you don't know rather than guessing. Don't investigate
or propose code in the issue unless asked: it's a record, not a plan.

## Working on an issue

1. Read it (`issue_read`), work on `dev` as usual.
2. Mention it in the commit message as **`Issue #12`** (on its own line;
   `Issue #3, #4` for several). **Don't write `Fixes #12`**: the repo's
   default branch is `dev` (so new Claude sessions start there and read the
   current CLAUDE.md), and GitHub closes "Fixes" issues as soon as the commit
   reaches the default branch, i.e. on Dev (this happened on test-app,
   Nov 2026).
3. The issue stays open through Dev, Alpha and Staging. When the fix is
   released to **Production**, the shared deploy's release step **closes
   it** with a comment naming the release (the release notes themselves
   never list issue numbers: they stay plain English) (e.g. "Released to Production in
   v2026.11.13.4"). It also recognises `Fixes`/`Closes`, as a safety net.
4. If you need to say something on the issue (a question, "done on Dev,
   waiting for release"), add a comment.
5. If it won't be done, close it with a comment saying why
   (`state_reason: not_planned`).

## Issue pills in release notes

When a release includes work done for an issue, the promote skill ends
that release-note bullet with `(#12)`. In the app's "What's new" panel it
shows as a small pill in the issue's label colour, e.g. **tweak #12**, as a
reference that it's been addressed (deliberately **not** a link). The
shared deploy looks the label up when it builds `releases.json`
(`"issues": {"12": {"label": "tweak", "color": "c5def5"}}`); if it can't,
the pill just says `#12`. On GitHub's release page `(#12)` is a normal link.

## Screenshots on issues

Claude can't use GitHub's drag-and-drop image upload, so screenshots go in
the repo and the comment shows them from there (tested Nov 2026):

1. Save the PNG in **`.github/issue-screenshots/<issue>-<before|after>.png`**
   on `dev` (with the fix, or in its own small commit). The deploy drops
   `.github/`, so these never appear on the live site.
2. Commit, push, then link it **pinned to that commit** so it never breaks:
   `https://raw.githubusercontent.com/<owner>/<repo>/<commit-sha>/.github/issue-screenshots/12-after.png`
   Check the link returns `200 image/png` before posting.
3. Comment with an HTML image tag so it can be sized and described:
   `<img src="<link>" alt="<what it shows>" width="360">`
   Typically a **Before** when the work starts and an **After** with
   "Done on Dev, closes when released to Production".

- Screenshot only what matters (one element or the card), at
  `deviceScaleFactor: 2`; typically 15–200 KB each.
- **Public repo = public screenshots.** Show test data only: sign in with a
  test account, never real users' names, emails or lists.
- Private repos: the same links need the viewer to be signed in to GitHub
  with access (not yet tested).

## Asking what's open

"What's open?" → `list_issues` (state open), then summarise grouped by type,
high priority first, with each issue's number and title.

## Privacy

Issues in a **public** repo are public: anyone can read them, and anyone
with a GitHub account can comment. Write them neutrally and never include
client names, emails or private details. For client work, make the app's
repo **private** (its issues become private too).
