# Starting a new app

Checklist for a new small web app (plain HTML/CSS/JS, no build step,
hosted on GitHub Pages, released through stages). Worked example:
`Thedodgykiwi/test-app`.

## The quick way: the `new-app` skill

1. **You:** create an **empty** repo on GitHub (a README is fine). Claude
   can't create repos from a cloud session.
2. Start a session with that repo (and the playbook) attached and say
   **"set up this repo as a new app"**. Claude asks the app's name, one
   sentence about it, and whether it needs sign-in, then runs
   `.claude/skills/new-app/new-app.sh`, which copies `templates/starter/`
   (a page with a small live example to delete (Preact components), the coloured stage banner
   with a subtle "Pipeline ↗" link, a top-right menu with theme, Settings
   and version / What's new, and dormant sign-in; nothing app-specific), fills in the names, pushes `main` and creates `dev`, `alpha`, `staging`.
   The first deploy also creates the issue labels.
3. **You:** three settings clicks (Pages source, deployment branches,
   default branch `dev`); Claude gives exact links, then re-runs the deploy
   and checks every stage address, the pipeline page and the labels.

The rest of this guide is what the skill does, for reference or for setting
up by hand.

## 1. Repo and branches

- [ ] User creates the repo on GitHub (Claude can't create repos from a
      cloud session). Public is needed for free GitHub Pages on a personal
      account, so **never commit secrets or personal data**.
- [ ] Add the repo to the Claude session (`add_repo`), clone it.
- [ ] Create the four stage branches from `main`: `dev`, `alpha`, `staging`, `main`.
      All work happens on `dev` (see `stages-and-releases.md`).

## 2. Copy the templates

From `templates/` in this repo:

| Template | Goes to | Change |
|---|---|---|
| `CLAUDE.md.template` | `CLAUDE.md` | app name, URLs, features to keep working |
| `.github/workflows/deploy.yml` | same path | `app_name` / `short_name` (and colours if wanted). Keeps `contents: write` (GitHub releases) and `issues: write` (shared labels) |

**Don't copy** the promote skill, the release-notes script or the deploy
steps: apps use the playbook's shared copies (see the README), so there's
only ever one version of each.

The app itself needs, at minimum:

- `index.html` with `<script src="stage.js"></script>` **before** the app
  script, and a `<div id="stage-banner" hidden></div>`.
- `stage.js` containing `window.STAGE = 'local';` (the deploy overwrites it
  per stage: never edit it for deploys).
- A stage banner shown on every stage except `main`, so nobody mistakes Dev
  for Production (see `github-pages.md`). Put a small "Pipeline ↗" link
  (`../pipeline/`) at its right end; hide it locally (no pipeline page there).
- `style.css` with `[hidden] { display: none !important; }`.
- Optional "What's new" panel that reads `releases.json` (generated at
  deploy time; 404 locally is normal).

## 3. One-time GitHub settings (the user does these)

- **Settings → General → Default branch:** `dev`. New Claude sessions start
  from the default branch (and read its CLAUDE.md), so they begin where the
  work happens. (Side effect: pull requests on GitHub target `dev` by
  default; issues are closed by the Production release, not by GitHub's
  "Fixes #n", see `issues.md`.)

- **Settings → Pages → Source:** GitHub Actions.
- **Settings → Environments → github-pages → Deployment branches:** choose
  **No restriction** (or list `main`, `staging`, `alpha`, `dev`). GitHub
  starts it on "Selected branches" with only `main`, which refuses the other
  stages' deploys.

## 4. Cloud session environment

Make a personal environment named after the repo with only the hosts the
app needs (see `cloud-sessions.md`). Add `<username>.github.io` so Claude
can check the live site after deploys.

## 5. Optional add-ons

- Sign-in and cloud data → `firebase-auth-and-firestore.md`
- Home-screen icons (PWA) → `pwa-icons.md`
- Icons in the UI: pick **one** icon set and stick to it (test-app uses
  Phosphor (test-app: duotone; the starter: Regular), copied into `icons.js`, no CDN; licence file in
  `LICENSES/`). Don't mix in emoji for UI controls.

## 6. First deploy

Push to `dev`, confirm the Actions run succeeded, open the Dev URL. Then
promote through the stages once so every URL exists.
