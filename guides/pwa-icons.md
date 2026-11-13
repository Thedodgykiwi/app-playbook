# Home-screen icons (PWA)

So the app can be "installed" (Add to Home Screen) with a proper icon,
different per stage so testers can tell Dev from Production.

## Setup

- `manifest.webmanifest` with `name`, `short_name`, `theme_color`, icons
  (192, 512, maskable 512).
- In `index.html`: `<link rel="manifest">`, `<link rel="apple-touch-icon"
  sizes="180x180">`, favicons, `<meta name="theme-color">`.
- One icon set per stage in `icons/app/<stage>/` (plus `local/`), one
  colour per stage. test-app generates them with `tools/make-app-icons.js`
  (Playwright renders an SVG glyph on a gradient to PNGs).
- Files in the repo point at `icons/app/local/` and say "<App> Local"; the
  deploy swaps in each stage's folder, name and theme colour. Don't
  hand-edit per stage.

## iOS quirk (iOS 27, tested on a real iPhone, Nov 2026)

Add to Home Screen **ignores linked icon files and manifest icons** and
shows a letter tile. Workaround: the deploy embeds the stage's
`apple-touch-icon.png` into `index.html` as a `data:` URI (step in
the playbook's shared `.github/workflows/deploy-stages.yml`). Keep it until Apple fixes this.

After any icon change, the user must **delete and re-add** the home-screen
shortcut to see it; iOS doesn't refresh existing ones.

## Works offline + install (the starter's `pwa.js` and `sw.js`)

Chosen from a mock-up (option B): "Install app" in the menu, plus a one-time
tip at the bottom from the **2nd visit** (never the first), hidden for good
once dismissed or installed.

- **Service worker per stage.** Registered as `sw.js` from each stage's
  folder, so its scope is that folder. Production's scope (`/app/`) contains
  the test stages (`/app/dev/` …), so its worker **ignores** those folders.
- **Fetching:** the page network-first (newest when online, saved copy
  offline); files stamped `?v=<build>` by the deploy cache-first (new build =
  new address, so never stale; older builds of a file are dropped); other
  own files network-first; the Firebase SDK from gstatic cache-first (its
  URL is versioned). Sign-in/database requests are left alone.
- **On install** the worker saves the page and every `?v=` file it links,
  so the app opens offline after one visit.
- **"New version ready":** the page compares its own `pwa.js?v=` build with
  the live page's (on load and when the app comes back into view) and shows
  a Reload bar. No byte-changing of `sw.js` needed.
- **Install:** Chrome/Edge/Android fire `beforeinstallprompt`: keep it and
  call `prompt()` from the menu or tip. **iPhone/iPad can't install from a
  button**: show a how-to (Share → Add to Home Screen → Add). Hide
  everything once `display-mode: standalone` (or `navigator.standalone`).
- Keys in browser storage include app **and** stage (`pwa:<app>:<stage>`).
- **iPhone Home Screen apps have their own storage**, separate from Safari:
  the installed app must be opened from its icon **online** once to save its
  offline copy. Otherwise, offline it shows a **blank white screen** (found
  on a real iPhone). So: the worker re-saves the page on every online visit
  (pwa.js messages it), the menu shows "✓ Ready to use offline" once saved,
  and an offline navigation with nothing saved gets a short built-in
  "You're offline" page instead of a blank one.
- **Don't trust `navigator.onLine` alone:** an iPhone Home Screen app in
  Airplane mode loaded from the offline copy but showed no offline strip.
  pwa.js also sends a tiny `HEAD ./?connection-check=<time>` (the worker
  never answers it from the saved copy) on load, when the app comes back
  into view, and every 30 s while offline. Remember Airplane mode can leave
  Wi-Fi on.
- **Testing:** build a local copy shaped like the deploy (Production folder
  with `dev/` inside, files stamped `?v=`), then in Playwright: reload while
  `context.setOffline(true)`, change the stamp to see the update bar, and use
  `devices['iPhone 13']` for the iPhone flow. The real install still needs a
  real phone.
