# Logging issues and requests (GitHub Issues)

Use each app's **GitHub Issues** as its to-do list: bugs, feature requests,
small tweaks and slowness reports, logged as they come in and worked on
later. Claude creates, lists, updates and closes issues with the GitHub
tools (`issue_write`, `list_issues`, `issue_read`, `add_issue_comment`).

## The choice card: how every request starts

Whenever the user raises a **feature, fix, tweak or idea** for an app, Claude
first shows a **choice card** (the AskUserQuestion tool: tappable options in
the Claude app), one card per request, with these options and the
recommended one first, marked "(Recommended)":

1. **Log it, build later**: create the issue only.
2. **Log it + mock-up first**: create the issue, then a clickable mock-up
   (2–3 options, `working-with-the-user.md`) before building. Recommend for
   new features or noticeable changes with more than one reasonable design.
3. **Build it now**: create the issue, build on Dev, commit with
   `Issue #<n>`. Recommend for small tweaks and clear bug fixes.

**Every issue uses the layout in "Writing a good issue" below** (What's
happening / what's wanted, Where, Expected, Reported by, Notes), however it
was created: from the card, logged after the fact, or by "log it". (Found in
test-app: issues #10–#16 were first written in a looser style and had to be
rewritten.)

Say in the card's question what the request is in one line (the card may be
all the user sees). Skip the card only when the user already said which
(e.g. "log it", "mock it up", "just do it", "promote …"), for questions that
change nothing, and for follow-ups inside work already chosen (they go on the
same issue). Every option creates an issue. Test-bench apps and the playbook
itself don't use issues: there the card offers mock-up first / build now.

## Every change gets an issue (automatically)

In an app, **every bug the user reports and every change they ask for gets
an issue, without being asked**: create it (label `bug`, `feature`, `tweak`
or `performance`) **before** starting work, then commit with `Issue #<n>`.
That gives each change a record, a pill in the release notes, and an
automatic close on the Production release. Small follow-ups during the same
piece of work ("move it 2px") go on the same issue.

**A new feature or behaviour is a new issue, even mid-session.** Follow-ups
are fixes and tweaks to what that issue asked for (a bug in it, a colour, a
layout fix). Something the issue didn't ask for ("add a Due tomorrow panel"
while building due dates) gets its own issue and the choice card first.
(Found in test-app, Nov 2026: the user had to remind Claude.)

Not for: the playbook itself, or a test-bench app like Playbook Trial
(starter work is recorded in the playbook's commits).

If work was done without one, log it afterwards ("Logged after the fact",
with the commits) and link it with a later commit that says `Issue #<n>`
(e.g. the commit that records the rule or a note), so the release still
closes it. (Found in test-app, Nov 2026: three changes had no issues.)

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
| `rollback` | Created automatically when Production is rolled back (with `bug`): why, and what needs fixing |

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

**A bug caused by another issue's change → make it a sub-issue** of that
issue, so the link shows on both (GitHub tools: `sub_issue_write`, method
`add`, parent = the issue **number**, `sub_issue_id` = the child's **id**,
the long number returned when it was created, not `#7`). Also say so in the
bug's Notes ("Caused by the change for #6").

**Screenshots in an issue.** The GitHub tools can't upload an image to an
issue. Save it (as a JPEG, to keep the repo small) under
`docs/issue-images/<short-name>.jpg` on `dev`, push, and put it in the
issue body as
`![what it shows](https://raw.githubusercontent.com/<owner>/<repo>/dev/docs/issue-images/<short-name>.jpg)`.
Only in a public repo, and check the screenshot shows no private details first.

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
