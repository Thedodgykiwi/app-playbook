# Starting a new app

Checklist for a new small web app (plain HTML/CSS/JS, no build step,
hosted on GitHub Pages, released through stages). Worked example:
`Thedodgykiwi/test-app`.

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
  for Production (see `github-pages.md`).
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
- **Settings → Environments → github-pages → Deployment branches:** allow
  `main`, `staging`, `dev`, `alpha` (otherwise non-main deploys are refused).

## 4. Cloud session environment

Make a personal environment named after the repo with only the hosts the
app needs (see `cloud-sessions.md`). Add `<username>.github.io` so Claude
can check the live site after deploys.

## 5. Optional add-ons

- Sign-in and cloud data → `firebase-auth-and-firestore.md`
- Home-screen icons (PWA) → `pwa-icons.md`
- Icons in the UI: pick **one** icon set and stick to it (test-app uses
  Phosphor duotone, copied into `icons.js`, no CDN; licence file in
  `LICENSES/`). Don't mix in emoji for UI controls.

## 6. First deploy

Push to `dev`, confirm the Actions run succeeded, open the Dev URL. Then
promote through the stages once so every URL exists.
