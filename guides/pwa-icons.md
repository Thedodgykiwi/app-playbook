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
`templates/.github/workflows/deploy.yml`). Keep it until Apple fixes this.

After any icon change, the user must **delete and re-add** the home-screen
shortcut to see it; iOS doesn't refresh existing ones.
