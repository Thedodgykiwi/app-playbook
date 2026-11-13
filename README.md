# app-playbook

Essential guide for new app development: step-by-step guides, gotchas and
copy-ready templates for building small web apps with Claude. The apps are
plain HTML/CSS/JS, hosted on GitHub Pages, released through stages
(dev → alpha → staging → main), optionally with Google sign-in and a cloud
database (Firebase).

Everything here was learned building `Thedodgykiwi/test-app`, which is the
worked example for all of it.

## For Claude: how to use this

When a project points you here, **read only the guides relevant to the
task**, follow their order of steps, and copy from `templates/` rather than
writing from scratch. If you learn something new (a gotcha, a missing step,
something that changed), add it to the right guide in the same session; see
`CLAUDE.md`.

## Guides

| Guide | Use it when |
|---|---|
| [new-app-setup.md](guides/new-app-setup.md) | Starting a new app from nothing |
| [stages-and-releases.md](guides/stages-and-releases.md) | Promoting dev → alpha → staging → main, release notes, hotfixes |
| [github-pages.md](guides/github-pages.md) | Deploying; caching; several stages on one site |
| [firebase-auth-and-firestore.md](guides/firebase-auth-and-firestore.md) | Adding Google sign-in and saving user data in the cloud |
| [pwa-icons.md](guides/pwa-icons.md) | Home-screen icons (including the iOS workaround) |
| [cloud-sessions.md](guides/cloud-sessions.md) | Claude running in a cloud session: network, logins, files that vanish |
| [working-with-the-user.md](guides/working-with-the-user.md) | How to communicate, concept mock-ups, guardrails, pre-push checklist |
| [preact.md](guides/preact.md) | Building app screens with Preact + htm + Signals (React-style, no build step) |
| [design.md](guides/design.md) | Look and feel, stage colours, icons, UI patterns that worked |
| [issues.md](guides/issues.md) | Logging bugs, feature requests and tweaks as GitHub issues ("log it" = record only) |

## Templates

| Path | What it is |
|---|---|
| `templates/CLAUDE.md.template` | Starter instructions for a new app's repo |
| `templates/.github/workflows/deploy.yml` | The small deploy file each app keeps: it just calls the shared deploy below |
| `templates/starter/` | The starting point every new app gets: a small live example (Preact) to delete, the coloured stage banner with a Pipeline link, a ready-made look (style kit + style guide page, accent colour setting), a menu with theme (light/dark/auto), Settings and version / What's new, works offline and installs to the home screen, and dormant sign-in (copied once; it's the app's own code after that) |
| `templates/firebase/` | Firebase config, rules, rules tests, `sync.js` sign-in + sync module |

## Starting a new app

Create an empty repo on GitHub, attach it and this playbook to a session, and
say **"set up this repo as a new app"**: the `new-app` skill copies
`templates/starter/` (a page with a small live example to delete, React-style components (Preact), the style kit and stage banner, plus Google
sign-in that stays dormant until switched on), creates the four stage
branches and walks you through the three GitHub settings. See
[new-app-setup.md](guides/new-app-setup.md).

## Shared by every app (one copy only)

These are **used directly from this repo**, never copied into apps, so they
can't drift apart. Improve them here and every app gets the change.

| Path | What it is |
|---|---|
| `.claude/skills/new-app/` | The **new-app** skill: sets up an empty repo as an app from `templates/starter/` |
| `.claude/skills/promote/` | The **promote** skill (dev → alpha → staging → main, release notes). Available in any session that has this repo attached |
| `.github/workflows/deploy-stages.yml` | The multi-stage GitHub Pages deploy. Apps call it from their small `deploy.yml` |
| `.github/scripts/release_notes.py` | Builds each stage's "What's new" from promotions (used by the shared deploy) |
| `.github/labels.json` + `.github/scripts/sync_labels.py` | The shared issue labels (bug, feature, tweak, performance, priorities), kept in place in every app by the shared deploy |
| `.github/scripts/pipeline_page.py` | Builds each app's **Pipeline page** (`…/<repo>/pipeline/`): what's live, what's waiting at each stage, open issues. Rebuilt by the shared deploy |
| `.github/scripts/make_releases.py` | Creates a dated GitHub release (`v2026.11.13`, `v2026.11.13.2` …) for every Production release (used by the shared deploy) |

Changing a shared file changes **every** app's next deploy or promotion:
test the change on one app's `dev` first.

## Pointing a new app at this playbook

Add this near the top of the new app's `CLAUDE.md` (the template already has it):

```markdown
## Playbook

General processes, design patterns and gotchas live in
https://github.com/Thedodgykiwi/app-playbook. Before setting up anything it
covers (new app, stages, deploys, Firebase, icons, design), attach that repo
to the session and read its README and the relevant guide.

**Keep the playbook growing.** Whenever work on this app teaches something
that would help *any* app (a gotcha, a missing or wrong step, a setup
process, a design or wording pattern that worked), update the right guide
in the playbook in the same session, commit it to the playbook's `main`, and
tell the user what was added. App-specific facts stay in this file instead.
```
