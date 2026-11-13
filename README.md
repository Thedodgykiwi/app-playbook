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

## Templates

| Path | What it is |
|---|---|
| `templates/CLAUDE.md.template` | Starter instructions for a new app's repo |
| `templates/.github/workflows/deploy.yml` | Multi-stage GitHub Pages deploy |
| `templates/.github/scripts/release_notes.py` | Builds "What's new" from promotions |
| `templates/.claude/skills/promote/` | The promote skill (dev → alpha → staging → main) |
| `templates/firebase/` | Firebase config, rules, rules tests, `sync.js` sign-in + sync module |

## Pointing a new app at this playbook

Add this near the top of the new app's `CLAUDE.md` (the template already has it):

```markdown
## Playbook

General processes and gotchas live in https://github.com/Thedodgykiwi/app-playbook.
Before setting up anything it covers (new app, stages, deploys, Firebase,
icons), attach that repo to the session and read its README and the relevant
guide. Add anything new you learn back to the playbook.
```
