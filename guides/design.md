# Design: patterns and lessons

Design decisions that worked and are worth reusing. Add to this whenever a
project teaches something about look, layout, wording or interaction that
would help other apps. Worked example: `Thedodgykiwi/test-app`.

## Process

- **Concept first for visible changes:** offer a clickable mock-up (Claude
  artifact, 2–3 options side by side, sample data, "Good / Watch out" per
  option). Iterate until the user picks. Details in `working-with-the-user.md`.
- **Match the app's existing look** in mock-ups and new features: same
  colours, radius, spacing, icon style.
- **Check visually.** Screenshot desktop and ~375 px phone width; don't
  trust element state alone (see the `[hidden]` gotcha in `github-pages.md`).

## Base look (test-app)

- System font (`system-ui, sans-serif`), light grey page (`#f4f5f7`), dark
  text (`#1d1f23`), one white card (`width: min(420px, 92vw)`, radius 12px,
  soft shadow). Buttons radius 8px, primary blue `#3b5bdb`.
- Simple, calm, lots of space; one main action colour.

## Stage colours (used for banner, home-screen icon, theme colour)

| Stage | Colour |
|---|---|
| Production (`main`) | blue `#3b5bdb` (no banner) |
| Staging | orange `#e67700` |
| Alpha | pink `#c2255c` |
| Dev | purple `#7048e8` |
| Local | grey `#495057` |

Non-production stages always show a fixed banner ("DEV environment") so
nobody mistakes them for the real app.

## Icons

- **One icon set, one style.** test-app uses Phosphor Icons, duotone only,
  copied into the app (`icons.js`, no CDN), with the licence in `LICENSES/`.
  Icons sized to the text (`1.2em`) and coloured with `currentColor`.
- No emoji for UI controls (fine as signposts in release notes).

## Patterns that worked

- **Sign-in in the card's top-right corner** (chosen from a 3-option
  concept). Signed out: a small "Sign in" button with the Google logo.
  Signed in: a round avatar with the first initial plus a small **sync dot**
  (green saved / amber saving / grey offline / red error) that opens an
  account menu (name, email, sync status in words, Sign out).
- **Status in words, not only colour:** the sync dot has a matching text
  line and `aria-label`, so it works for colour-blind and screen-reader users.
- **Toasts** (short message at the bottom, `role="status"`) for things that
  happened in the background: "2 to-dos from this device were added to
  your account", "Signed out. Showing the to-dos saved on this device."
- **Menus:** close on Escape and on clicking outside; return focus to the
  button that opened them; `aria-expanded` on the button.
- **Friendly error messages** that say what to do ("Allow pop-ups for this
  site and try again"), not error codes; stay silent when the user simply
  cancelled.
- **"What's new" panel** reading release notes, so testers see what changed
  on each stage.
- **Top-right app menu** (the starter's `menu.js`, chosen from 3 mock-ups):
  Google photo + name when signed in; Theme as a Light / Auto / Dark
  segmented switch right in the menu (one tap); Settings row opening a panel;
  Sign out; a thin line, then the version ("Version 2026.11.13", or "Dev
  build abc1234") linking to What's new. Works with sign-in off too.
- **Light / dark theme:** colours only via CSS variables on `:root`, with a
  `data-theme` of light / dark / auto (auto = `prefers-color-scheme`).
  Apply the saved choice in an inline `<head>` script so the page never
  flashes the wrong theme on load.
- **iPhone underlines emails/phone numbers** shown as text (Safari data
  detectors): add `<meta name="format-detection" content="telephone=no, email=no, address=no">`.
- **Style kit (starter, chosen from 3 mock-ups: "B", neutral + accent):**
  shadcn/ui-like look in plain CSS (no Tailwind/React: they need a build
  step or a CDN). Tokens as CSS variables; components `.btn`, `.input`,
  `.select`, `.check` (checkbox/radio/switch), `.card`, `.badge`, `.list`,
  `.notice`, `.empty-state`; `styleguide.html` shows each with copy-ready
  HTML. The global `button` rule is a plain reset, so nothing leaks.
- **Accent colour setting:** six accents (blue, purple, green, teal, orange,
  pink), each with a light value (white text, ≥4.5:1) and a lighter dark-mode
  value with dark text. Theme rules pick `--a-l` or `--a-d`, so accents and
  themes combine without extra rules. Green had to be darkened (#237032) to
  pass contrast.
- **Icons: Phosphor Regular** (outline) for new apps and test-app (since its new look; its home-screen icons stay duotone).
- **Groups inside a collapsible section:** don't nest another row of toggle
  headings (feels like a menu inside a menu). Use centred divider labels
  ("─── Today · 2 ⌃ ───") that hide/show their own items (test-app's Done).
- **Empty, loading and error screens (starter, style "C": big illustration
  on a soft colour blob):** `ui.js` has `EmptyState` (icon, title, text,
  action) and skeletons (`SkeletonRows`, `SkeletonCard`, `SkeletonTable`;
  shimmer off with Reduce Motion). `error-screen.js` shows "Oops, something
  went wrong" (Try again / Report a problem → pre-filled GitHub issue) if the
  app fails **while loading**; the app calls `AppReady()` once its first
  screen is drawn. Static hosting has no server errors, so there's no "500".
  The shared deploy adds a site-wide **404 page** (`.github/templates/404.html`):
  one per app for all stages, it links back to the stage the address was in.
  Big illustrations use Phosphor **duotone** (`<name>-duotone` in icons.js);
  everything else stays Regular.
- **Toasts (starter `toast.js`):** `AppToast.show(message, { icon, action: { label, icon, onClick }, duration })`.
  Dark rounded card near the bottom, slide-up entrance, fades after 4 s (6 s
  with an action), one at a time, `role="status"`, Reduce Motion respected.
  While one shows, the install tip and "new version" bar step aside. Apps
  with a fixed bottom bar set `--toast-bottom`. Use an action for anything
  undoable ("moved to Done · Undo") instead of asking "are you sure?".
- **Swipe actions on list rows** (test-app: swipe right to star): put the
  row's content in an inner element that slides over a coloured layer
  ("★ Star"); `touch-action: pan-y` so vertical scrolling still works; only
  start dragging after ~10px of mostly-sideways movement; act past a
  threshold (~70px); swallow the click that follows so it isn't also a tap.
  Swipes are hidden, so always offer the same action somewhere visible too
  (test-app: a switch in the edit sheet) and show a one-time tip.
- **Sheets that can grow taller than a phone: pin the action buttons.** Make
  the Cancel/Save row `position: sticky; bottom: 0` with the sheet's
  background and a top border, and size the sheet with `dvh` (not `vh`) so
  iPhone toolbars don't hide its bottom. Otherwise Save scrolls off-screen
  and people miss it. (Found in test-app, Nov 2026, after adding a calendar.)
- **Rows with a layer underneath (swipe actions) must never go see-through.**
  Any highlight or fade on the row (e.g. a "just edited" flash) should fade to
  the row's own colour, not `transparent`, or the coloured action layer flashes
  through. (Found in test-app, Nov 2026: a gold flash after every edit.)
- **Smooth fold/collapse of a section:** wrap the content in a
  `display: grid; grid-template-rows: 1fr` box (child `min-height: 0;
  overflow: hidden`) and animate to `0fr`. Unlike `max-height`, it never
  cuts off a long list. Give the child a little padding (and matching
  negative margin) so card shadows aren't clipped, mark the folded content
  `inert` so the keyboard skips it, and skip the animation under Reduce
  Motion. (test-app, Nov 2026: tap a panel heading to fold it.)
- **Panels** (Settings, What's new): `<dialog>` with `showModal()` (focus,
  Escape and backdrop for free); bottom sheet on phones, centred box on
  wider screens.
- **Issue pills** at the end of a release note ("tweak #2"): small rounded
  pill in the GitHub label's colour, `.72rem` bold, text dark or white
  (whichever contrasts more with the colour), kept on the same line as the
  word before it (`white-space: nowrap` wrapper), **not a link**: it's a
  quiet reference that a reported issue was dealt with. Code:
  test-app's `whats-new.js` (`pill()`).

## Gotchas

- **Newspaper-style columns of cards (`columns: 3`)**: give each card
  `display: table; width: 100%; break-inside: avoid; -webkit-column-break-inside: avoid`.
  With plain `display: block`, Safari still splits a card across two columns
  (a stray border line appears at the top of the next column); with
  `inline-block` it stays whole but the columns stop balancing (two cards
  both land in the first column). Edit 1 Job Board, Nov 2026.

- **A menu that closes on "click outside" also closes when your own code
  clicks a hidden button** (e.g. a menu item that works by calling
  `someButton.click()`): that click bubbles to `document` from outside the
  menu. Only close on real clicks: `if (e.isTrusted && !e.target.closest('.menu')) close()`.
  (Edit 1 Job Board, Nov 2026: the theme choice shut the profile menu.)

- **Hover sticks on phones:** after a tap, iPhone Safari keeps a button's
  `:hover` look until you tap elsewhere (e.g. a grey box stayed behind
  "Medium" on test-app's priority flag). For buttons tapped repeatedly in
  place (toggles, cycling flags), put the hover style inside
  `@media (hover: hover) { … }` so only mouse devices get it.

- **One-line text (`white-space: nowrap` + ellipsis) can push a whole page
  off-screen** when it sits in a CSS grid or flex column: the column grows to
  fit the text. Give the column `grid-template-columns: minmax(0, 1fr)` (or
  `min-width: 0` on flex children). Test with the **longest real content**
  (e.g. a long release headline), not just sample data: found on a real
  iPhone in test-app.

- **Global element styles leak into new components.** test-app has
  `button:hover { background: <blue> }`; a new button styled with
  `.news-open { all: unset }` still turned solid blue on hover, because
  `button:hover` is more specific than a single class. When adding a
  component made of buttons/links, give it its own `:hover` and
  `:focus-visible` rules, and **check hover and focus in the browser**
  (Playwright `hover()`, then screenshot), not just the resting state.

- **Pop-ups and sheets must not disturb what's behind them.** Opening one
  should only *add* the panel: don't redraw the list underneath (it
  flickers), fade the dark backdrop in with the panel instead of snapping
  it on, and move the cursor in with `focus({ preventScroll: true })` so
  the page doesn't jump. Redraw the list only after Save. (Spotted by the
  user in test-app's edit-sheet mock-up.)

## Wording

- **Confirm dialogs:** ask about the action ("Biff this job?", not "Has this
  job been biffed?"), name the thing, say what happens and whether it can be
  undone, and label the buttons with the action ("Keep job" / "Biff job", never
  "No / Yes"). Put focus on the safe button, not the ✕. If the app has an Undo
  bar, don't ask at all by default; offer the question only as a setting.
  (Edit 1 Job Board, issue #13.)

- Plain, friendly, short. Say what the user can do or see.
- Explain anything technical in brackets the first time.
