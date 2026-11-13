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
2. Mention it in the commit message: **`Fixes #12`** (or `Closes #12`).
   GitHub closes the issue automatically when that commit reaches the
   default branch, `main`, i.e. **when the fix is live in Production**,
   not when it's only on Dev. Until then it stays open.
3. If you need to say something on the issue (a question, "done on Dev,
   waiting for release"), add a comment.
4. If it won't be done, close it with a comment saying why
   (`state_reason: not_planned`).

## Asking what's open

"What's open?" → `list_issues` (state open), then summarise grouped by type,
high priority first, with each issue's number and title.

## Privacy

Issues in a **public** repo are public: anyone can read them, and anyone
with a GitHub account can comment. Write them neutrally and never include
client names, emails or private details. For client work, make the app's
repo **private** (its issues become private too).
