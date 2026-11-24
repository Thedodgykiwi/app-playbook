# Hosting on GitHub Pages (several stages, one site)

Each app has a small `.github/workflows/deploy.yml` (from
`templates/`) that runs on a push to any stage branch and calls the
playbook's **shared** deploy, `.github/workflows/deploy-stages.yml`. The
shared deploy is the only copy of the steps, so improve it there. It checks out **all four** stage branches and
rebuilds the whole site: `main` at the root, the others in sub-folders.
Per stage it:

- writes `stage.js` (`window.STAGE = '<stage>'`)
- builds `releases.json` from promotion commits ("What's new")
- adds `?v=<commit>` to CSS/JS/icon/manifest links (cache-busting)
- swaps in that stage's home-screen icons, app name and theme colour
- embeds the stage's `apple-touch-icon.png` as a `data:` URI (iOS quirk, see `pwa-icons.md`)
- removes `.git` and `.github` from the published copy

Everything else in the branch is published, including `CLAUDE.md`, tests
and rules. That's fine for a public repo, but it's another reason to keep
secrets out.

## Gotchas

- **Caching:** GitHub Pages caches pages for up to 10 minutes. CSS/JS are
  cache-busted, but `index.html` can be briefly stale. Tell users:
  hard refresh (Ctrl/Cmd+Shift+R).
- **One web address for all stages** (`<user>.github.io`). Browser
  storage, cookies, service workers and sign-in are **shared** between
  stages. Key everything stored in the browser by stage:
  `` const storageKey = `todos-${window.STAGE || 'local'}`; ``
  It's also shared by **every app** on that address (`/test-app/`,
  `/playbook-trial/` …): put the app's folder in keys too, e.g.
  `` `prefs:${location.pathname.split('/')[1]}` `` (the starter does this).
- **Stage banner:** show the stage name ("DEV", "ALPHA"…; no "environment", too long on phones) on every stage except
  `main`, coloured per stage, so nobody mistakes a test stage for Production.
  Locally it says "LOCAL".
- **`hidden` attribute vs CSS:** a rule like `.thing { display: flex }`
  beats the `hidden` attribute and the element stays visible. Add
  `[hidden] { display: none !important; }` to the stylesheet, and check UI
  changes from a **screenshot**, not by reading element state.
- Deploys are cancelled if a newer one starts (`concurrency: pages`), so
  two quick pushes give one deploy of the latest. On GitHub's commit list
  the older commit then shows a red ✗ (e.g. "2 / 3": a step was
  *cancelled*, not failed). Harmless if a later run succeeded; only a ✗ on
  the **latest** commit needs looking at. Avoid starting a manual run while
  a deploy is still going.
- **"No artifacts named github-pages were found"** in the deploy step (with
  "Is githubstatus.com reporting issues…") is a GitHub hiccup, not your
  code. The shared deploy now tries the publish step a second time after 30 s
  by itself (it failed three runs in a row on test-app's Alpha, Nov 2026). If
  it still fails, start a fresh run on the branch (`run_workflow`) a few
  minutes later.
- Local preview: `python3 -m http.server 8080` from the repo root.

## Search engines

- **Test stages are hidden from search engines:** the shared deploy adds
  `<meta name="robots" content="noindex, nofollow">` to every page on Dev,
  Alpha and Staging, so half-finished versions never turn up in Google.
  Production is left alone. (A `robots.txt` can't do it: it only works at the
  very top of the domain, which a project site doesn't own.)
- Pages that should never be indexed even on Production (the style guide, the
  pipeline page, 404) carry their own `noindex`.

