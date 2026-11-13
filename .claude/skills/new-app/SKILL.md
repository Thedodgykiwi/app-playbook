---
name: new-app
description: Set up a brand-new, empty GitHub repo as an app from the playbook's starter, with the four stage branches (dev, alpha, staging, main), the shared deploy, issue labels, pipeline page and an optional Google sign-in module. Use when the user asks to start, create or set up a new app or project, or says "set up this repo as a new app".
---

# Set up a new app

This skill lives in the **app-playbook** repo (one copy, shared by every
app). The starter it copies is `templates/starter/` in the playbook. The new
app uses the playbook's shared deploy, promote skill, labels and pipeline
page from then on.

## What the user does vs. what Claude does

- **User:** creates an **empty** GitHub repo (no template; a README is
  fine) and starts a session with it attached; then does three settings
  clicks (step 4). Claude **can't create repos** from a cloud session.
- **Claude:** everything else, below.

## Steps

1. **Check the basics.** The new repo is attached and cloned, the playbook
   is attached too. If the repo is **private**, warn: GitHub Pages on a
   private repo needs a paid GitHub plan, and the pipeline/promote checks
   that use the public API won't work. Ask whether to go ahead.

2. **Ask the user** (one message):
   - the app's **name** (shown in the app and stage banner) and a short
     name for home-screen icons (default: same);
   - **one sentence** saying what it's for;
   - an **icon idea** for the home screen (any Phosphor icon, e.g. "a
     calendar", "a shopping cart"; default: the starter's neutral app tiles);
   - does it need **Google sign-in / cloud-saved data**? (Default: not now;
     the module ships dormant either way, see step 6.)

3. **Run the setup** from the new repo's root (preview first):

       <skill-dir>/new-app.sh --name "<name>" --short "<short>" --description "<sentence>" --dry-run
       <skill-dir>/new-app.sh --name "<name>" --short "<short>" --description "<sentence>"

   It refuses to touch a repo that already has app files or stage branches.
   It copies the starter, fills in the names, pushes `main`, creates
   `staging`, `alpha`, `dev`, and reports the first deploy (which is
   **expected to fail** until Pages is switched on) and the issue labels.

   If they gave an icon idea, pick the matching Phosphor icon, make the icons
   on `dev` with `tools/make-app-icons.js` (see `guides/pwa-icons.md`), show
   them a picture of the five stage icons, commit and push.

4. **Give the user the three GitHub settings**, with direct links
   (`https://github.com/<owner>/<repo>/settings/...`), in this order:
   1. **Pages** (`/settings/pages`): Build and deployment → Source:
      **GitHub Actions**.
   2. **Environments** (`/settings/environments`) → `github-pages` →
      Deployment branches and tags → choose **No restriction** (one tap,
      saves itself; fine when only the owner can push). GitHub starts it on
      "Selected branches" with only `main`, which blocks the other stages. (If `github-pages` isn't listed
      yet, do step 1 first and refresh.)
   3. **General** (`/settings`) → Default branch → switch to **`dev`** (so new
      Claude sessions start where the work happens).

5. **When they say it's done, verify:**
   - re-run the deploy on `dev` (GitHub tools: `actions_run_trigger`,
     `run_workflow`, workflow `deploy.yml`, ref `dev`) and wait for success;
   - the app answers at `/`, `/dev/`, `/alpha/`, `/staging/` and `/pipeline/`
     (each shows the empty placeholder page, no errors; Dev/Alpha/Staging show
     their coloured stage banner with a working "Pipeline ↗" link, Production none);
   - the labels exist (`bug`, `feature`, `tweak`, `performance`,
     `priority: high/low`, `rollback`);
   - default branch is `dev` (`curl -s https://api.github.com/repos/<owner>/<repo> | grep default_branch`).
   Report each as passed or what's missing.

6. **Sign-in (only if they said yes):** follow `guides/firebase-auth-and-firestore.md`
   from step 0. The starter already has `account.js` and an empty
   `firebase-config.js`; the app's own data code and rules are written for
   this app (test-app's `sync.js` and `firestore.rules` are the worked
   example). Otherwise tell them it can be switched on later ("add sign-in
   to this app").

7. **Wrap up:** suggest the cloud environment / setup script if this account
   doesn't have them yet (`guides/cloud-sessions.md`), and say what to do
   next: describe the first feature ("log it", concept mock-up, build on Dev).
   The starter is deliberately blank: an empty box, the coloured stage
   banner (Dev/Alpha/Staging/LOCAL, none on Production) with a subtle
   "Pipeline ↗" link, and the top-right menu (`menu.js`): Google photo when
   signed in, Light/Auto/Dark theme, Settings (text size; add the app's own
   settings there), and the version at the bottom opening "What's new".
   It also works offline and can be installed (`pwa.js`, `sw.js`,
   `manifest.webmanifest`, per-stage icons in `icons/app/`): offline strip,
   "new version ready" bar, "Install app" / "Add to Home Screen" in the
   menu, and a one-time tip from the 2nd visit.
   Optional extra from test-app, only when asked: the news bar (`guides/design.md`).

## Updating this skill or the starter

Fix it here in the playbook (SKILL.md, `new-app.sh`, `templates/starter/`),
test on a practice repo, commit to `main`: the next new app uses the fix.
Apps already created own their copy of the starter files (they're the app's
code now); the shared parts (deploy, promote, labels, pipeline page) update
everywhere automatically.
