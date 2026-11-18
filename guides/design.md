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

## Base look

- The starter's style kit (`style.css`, live examples in `styleguide.html`)
  is the base look for every app: system font, calm neutral colours, one
  accent colour for main actions, Light / Dark / Auto. Use its variables and
  building blocks rather than new styles.
- Simple, calm, lots of space; one main action colour.

## Stage colours (used for banner, home-screen icon, theme colour)

| Stage | Colour |
|---|---|
| Production (`main`) | blue `#3b5bdb` (no banner) |
| Staging | orange `#e67700` |
| Alpha | pink `#c2255c` |
| Dev | purple `#7048e8` |
| Local | grey `#495057` |

Non-production stages always show a fixed banner with just the stage name
("DEV", "ALPHA", "STAGING") so nobody mistakes them for the real app. Just the
name: "DEV environment" made the banner's buttons overlap on phones (The
Shortlist #76).

## Icons

- **One icon set, one style:** Phosphor Icons, Regular (outline), copied into
  the app (`icons.js`, no CDN), with the licence in `LICENSES/`.
  Icons sized to the text (`1.2em`) and coloured with `currentColor`.
- No emoji for UI controls (fine as signposts in release notes).

## Patterns that worked

### Look: style kit, colour, theme

- **Style kit (starter, chosen from 3 mock-ups: "B", neutral + accent):**
  shadcn/ui-like look in plain CSS (no Tailwind/React: they need a build
  step or a CDN). Tokens as CSS variables; components `.btn`, `.input`,
  `.select`, `.check` (checkbox/radio/switch), `.card`, `.badge`, `.list`,
  `.notice`, `.empty-state`; `styleguide.html` shows each with copy-ready
  HTML. The global `button` rule is a plain reset, so nothing leaks.
- **Light / dark theme:** colours only via CSS variables on `:root`, with a
  `data-theme` of light / dark / auto (auto = `prefers-color-scheme`).
  Apply the saved choice in an inline `<head>` script so the page never
  flashes the wrong theme on load.
  **Every new colour needs three rules:** light on `:root`, then the same
  dark values twice: `:root[data-theme="dark"]` *and*
  `@media (prefers-color-scheme: dark) { :root[data-theme="auto"] … }`.
  Miss the second and dark mode looks right only when chosen by hand, not
  when following the phone: a mock-up's new label was unreadable on the
  user's phone (The Shortlist #43, Nov 2026). Check mock-ups and new UI in dark
  mode too (Playwright `colorScheme: 'dark'`), and aim for 4.5:1 contrast.
- **Colour palette: 12 evenly spread hues** (red, orange, yellow, lime,
  green, teal, cyan, blue, purple, grape, pink, graphite), shared by the
  accent setting and anything users colour themselves (lists, tags). If every
  colour must carry white text they drift to similar dark shades and look
  samey, so: **user colours** show as a **filled tile behind an icon** (bright
  colour, white or dark icon chosen per colour); the **accent** swatch shows
  the bright colour, but the light theme uses a deeper shade of the same hue
  (white button text and link text ≥4.5:1) and the dark theme the bright one
  with dark text (`--a-l` / `--a-d`, so accents and themes combine without
  extra rules). Lay swatches out in full rows (a fixed grid, 6 per row) so
  every phone shows the same rows. Keep the old default exactly as it was
  when widening a palette. (The Shortlist #72/#75; the starter has it.)
- **Levels (priority, urgency, strength): show them by shape as well as
  colour, with one symbol used everywhere.** Signal bars (3 filled = high,
  2 = medium, 1 = low, unfilled bars faint) read at a glance and for
  colour-blind users, where three same-shaped flags in different colours
  didn't. Use the same symbol in headings, rows, pickers and buttons. If
  other groups already use background colour (starred, due), keep level
  groups neutral and colour only the heading. (The Shortlist, Nov 2026.)

### Menus, panels and navigation

- **Top-right app menu** (the starter's `menu.js`, chosen from 3 mock-ups):
  a round photo / person button. **Signed out:** the menu opens with a small
  card ("Your to-dos, on every device / Sign in to keep them safe and in
  sync") and a full-width **Sign in with Google** button; a separate "Sign
  in" button beside the title looked awkward (a bright white box in dark
  mode) and crowded it (The Shortlist #78). **Signed in:** photo, name,
  email and a small **sync dot** (green saved / amber saving / grey offline /
  red error) with the status in words. Then Settings, Add to Home Screen,
  Sign out, and the version ("Version 2026.11.13" / "Dev build abc1234")
  opening What's new. Works with sign-in off too.
- **Appearance choices live together in Settings** (Theme Light / Auto /
  Dark, accent colour, text size, then the app's own display options), not
  the theme in the menu and the rest in Settings: people look for them in
  one place, and most set the theme once (Auto) (The Shortlist #77).
- **Switching between views of one list: a side panel, opened two ways.**
  For "My Day / Important / Planned / Completed / your own lists", a panel
  from the left (like Microsoft To Do) beat a chip row (gets crowded once
  people add their own lists) and a title-only menu (people don't guess the
  title is tappable). Open it from a "‹ Lists" button **and** by tapping the
  view's title ("My Day ▾"), give each view its own big title and a count,
  and keep the panel open as a sidebar on wide screens. Adding while a view
  is open should put the new item in that view. (The Shortlist #71, Nov 2026.)
- **Panels** (Settings, What's new): `<dialog>` with `showModal()` (focus,
  Escape and backdrop for free); bottom sheet on phones, centred box on
  wider screens.
- **Menus:** close on Escape and on clicking outside; return focus to the
  button that opened them (or the section heading if the button has gone);
  `aria-expanded` on the button. A menu tied to a section closes whenever
  the section folds or its button stops showing (data changed, synced away),
  not just hides, or it pops back open by itself later (found by
  `/code-review`, The Shortlist #59).
- **Edit panels: changes apply at once, with just Done** (and an Undo
  note), not Cancel / Save. Each tap (priority, date, colour, icon) saves
  straight away; text saves when you leave the box; Done, Esc or tapping
  outside closes. Use it for every edit panel in an app, so they all behave
  the same; a "new item" panel makes the item on Done only if it has a name.
  Put the Undo note **inside** the panel (see the dialog toast gotcha).
  Delete keeps a confirm step. (The Shortlist #60, #72.)
- **Sheets that can grow taller than a phone: pin the action buttons.** Make
  the actions row `position: sticky; bottom: 0` with the sheet's
  background and a top border, and size the sheet with `dvh` (not `vh`) so
  iPhone toolbars don't hide its bottom. Otherwise the buttons scroll off-screen
  and people miss it. (Found in The Shortlist, Nov 2026, after adding a calendar.)

### Lists and rows

- **Focused views get slim headings; the overview keeps its panels.** In a
  view that already filters the list (My Day, Planned, Important), big coloured
  group panels repeat what the view says. Small rounded "pill" headings by
  *when* (Overdue / Today / Tonight / a date) over plain cards fit about 50%
  more on screen. Hide the heading when there's only one group. If people
  disagree on the look, one Settings choice (e.g. Pills / Lines / Boxes) for
  all focused views is cheap when the styles share the same rows. (The
  Shortlist #71, Nov 2026.)
- **Groups inside a collapsible section:** don't nest another row of toggle
  headings (feels like a menu inside a menu). Use centred divider labels
  ("─── Today · 2 ⌃ ───") that hide/show their own items (The Shortlist's Done).
- **Smooth fold/collapse of a section:** wrap the content in a
  `display: grid; grid-template-rows: 1fr` box (child `min-height: 0;
  overflow: hidden`) and animate to `0fr`. Unlike `max-height`, it never
  cuts off a long list. Give the child a little padding (and matching
  negative margin) so card shadows aren't clipped, mark the folded content
  `inert` so the keyboard skips it, and skip the animation under Reduce
  Motion. (The Shortlist, Nov 2026: tap a panel heading to fold it.)
- **Swipe actions on list rows** (The Shortlist: swipe right to star): put the
  row's content in an inner element that slides over a coloured layer
  ("★ Star"); `touch-action: pan-y` so vertical scrolling still works; only
  start dragging after ~10px of mostly-sideways movement; act past a
  threshold (~70px); swallow the click that follows so it isn't also a tap.
  Swipes are hidden, so always offer the same action somewhere visible too
  (The Shortlist: a switch in the edit sheet) and show a one-time tip.
- **Rows with a layer underneath (swipe actions) must never go see-through.**
  Any highlight or fade on the row (e.g. a "just edited" flash) should fade to
  the row's own colour, not `transparent`, or the coloured action layer flashes
  through. (Found in The Shortlist, Nov 2026: a gold flash after every edit.)
- **Small, quiet buttons with a full-size tap area.** A section tool that
  shouldn't compete with its heading (e.g. "Tidy up" next to "Done") can look
  about 30px tall but still be easy to tap: `position: relative` plus
  `::before { content: ""; position: absolute; inset: -7px 0; }` gives a 44px
  tap area without changing the look. Show such tools only while their
  section is open (The Shortlist #59).

### Feedback and status

- **Toasts** (starter `toast.js`) for things that happened in the background or can be undone ("2 to-dos from this device were added to your account"): `AppToast.show(message, { icon, action: { label, icon, onClick }, duration })`.
  Dark rounded card near the bottom, slide-up entrance, fades after 4 s (6 s
  with an action), one at a time, `role="status"`, Reduce Motion respected.
  While one shows, the install tip and "new version" bar step aside. Apps
  with a fixed bottom bar set `--toast-bottom`. Use an action for anything
  undoable ("moved to Done · Undo") instead of asking "are you sure?".
- **Status in words, not only colour:** the sync dot has a matching text
  line and `aria-label`, so it works for colour-blind and screen-reader users.
- **Friendly error messages** that say what to do ("Allow pop-ups for this
  site and try again"), not error codes; stay silent when the user simply
  cancelled.
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
- **"What's new" panel** reading release notes, so testers see what changed
  on each stage.
- **Issue pills** at the end of a release note ("tweak #2"): small rounded
  pill in the GitHub label's colour, `.72rem` bold, text dark or white
  (whichever contrasts more with the colour), kept on the same line as the
  word before it (`white-space: nowrap` wrapper), **not a link**: it's a
  quiet reference that a reported issue was dealt with. Code:
  test-app's `whats-new.js` (`pill()`).

## Gotchas

### iPhone and Safari

- **iPhone Safari zooms into any text box under 16px** when it's tapped,
  and stays zoomed. A "Small" text size (e.g. 93.75% on `:root`) pushes rem
  sized boxes under 16px, so pin typing boxes to `max(16px, 1rem)` in that
  mode (the starter does). (The Shortlist #73, Nov 2026.)
- **`env(safe-area-inset-*)` is zero unless the viewport tag has
  `viewport-fit=cover`.** Without it, an installed iPhone web app puts the
  bottom bar right against the home-bar swipe line, even though the CSS
  "allows" for it. The starter's `index.html` now includes it; add left/right
  insets too so landscape notches don't cover content, **added to** the
  normal padding (`calc(1rem + env(safe-area-inset-left))`): setting
  `padding-left: env(...)` alone wiped the side margins, since the inset is 0
  on an upright phone (The Shortlist #65, Nov 2026).
- **Hover sticks on phones:** after a tap, iPhone Safari keeps a button's
  `:hover` look until you tap elsewhere (e.g. a grey box stayed behind
  "Medium" on test-app's priority flag). For buttons tapped repeatedly in
  place (toggles, cycling flags), put the hover style inside
  `@media (hover: hover) { … }` so only mouse devices get it.
- **Hide swipe-reveal layers at rest.** A coloured layer kept under a row for
  swipe actions (e.g. gold "Star") can show through on iPhone Safari, mostly
  inside embedded frames, until the row is touched (a repaint glitch). Keep
  it `visibility: hidden` and show it only while the row is being swiped or
  sliding back (The Shortlist #70, Nov 2026).
- **iPhone underlines emails/phone numbers** shown as text (Safari data
  detectors): add `<meta name="format-detection" content="telephone=no, email=no, address=no">`.
- **Newspaper-style columns of cards (`columns: 3`)**: give each card
  `display: table; width: 100%; break-inside: avoid; -webkit-column-break-inside: avoid`.
  With plain `display: block`, Safari still splits a card across two columns
  (a stray border line appears at the top of the next column); with
  `inline-block` it stays whole but the columns stop balancing (two cards
  both land in the first column). Edit 1 Job Board, Nov 2026.

### Layout and checking it

- **Changing a title or label's length: measure it against its neighbours at
  320, 360, 375 and 390px, signed out as well as signed in.** A longer app
  name ran under the "Sign in" button on narrow phones; nothing scrolled
  sideways, so the automatic check passed. Compare the text's right edge with
  the next control's left edge (Playwright `getBoundingClientRect`).
  (The Shortlist, Nov 2026: renamed to a longer name.)
- **Check alignment by measuring, not by eye.** In Playwright, compare the
  vertical centres (`getBoundingClientRect()`: `top + height / 2`) of the
  things that should line up (title text, arrow button, icon buttons) at
  desktop and phone width; aim for the same number. Screenshots taken
  mid-animation (e.g. an arrow rotating) look misaligned when they aren't.
  A heading with a small label above the title needs `align-items: flex-end`
  (plus a small nudge) for side buttons to line up with the title, not the
  label. (Edit 1 Job Board, issue #17.)
- **One-line text (`white-space: nowrap` + ellipsis) can push a whole page
  off-screen** when it sits in a CSS grid or flex column: the column grows to
  fit the text. Give the column `grid-template-columns: minmax(0, 1fr)` (or
  `min-width: 0` on flex children). Test with the **longest real content**
  (e.g. a long release headline), not just sample data: found on a real
  iPhone in The Shortlist.
- **Cards that hide overflow and hold an input: use `overflow: clip`, not
  `hidden`.** A `hidden` box is still a scroll container, so focusing an
  input inside (or `scrollIntoView`) can shift its content sideways and
  clip the edge. `clip` can't scroll. Also give grid/flex children that
  hold inputs `min-width: 0` so they shrink instead of overflowing
  (The Shortlist #44, Nov 2026).
- **A sidebar that stays open on wide screens must make room for fixed
  parts:** put it *under* the stage banner (lower z-index, padded down), or
  it covers the banner's left-end buttons; push the page over
  (`padding-left`), and re-centre any fixed bottom bar on the space that's
  left, not the whole window. (The Shortlist #71, Nov 2026.)
- **Refactoring CSS with proof of "no visible change"** (merging stylesheets,
  removing `!important`): take Playwright screenshots of ~15 views (desktop and
  phone, light and dark, open dialogs/menus, messages, bars) with the clock and
  other ticking text hidden and animations off; take them twice to prove they
  repeat. Then change one thing at a time, re-shoot, and keep the change only if
  every view is byte-identical. Serve the CSS from memory with `page.route` so
  each trial needs no file writes. Edit 1 Job Board (issue #24): 3 files → 1,
  41 of 52 `!important` removed automatically, 11 proved necessary.

### Colour

- **Coloured text on a tint of the same colour fails contrast.** A red
  "Overdue" label on a 14% red tint was only 3.4:1 (needs 4.5:1). Darken the
  text toward the body text colour, e.g. `color-mix(in srgb, var(--danger)
  75%, var(--text))`, which works in light and dark themes. (The Shortlist
  #71, Nov 2026.)

### Behaviour

- **A screen tied to something that can disappear must fall back.** If the
  open view is a list (or project, folder…) that's been deleted, on this
  device, another one, or with the account, show the overview instead of an
  empty screen, and keep the saved choice in case it comes back. Found
  testing "Delete my account" (The Shortlist #79).
- **Toasts are one line: keep them under about 40 characters** ("Your
  account has been deleted."); longer ones get cut off with "…" on phones.
- **Toasts don't show above an open `<dialog>`.** A modal dialog sits in the
  browser's top layer, so a page toast (e.g. "Saved · Undo") appears behind
  it and can't be tapped. Anything that applies changes while a dialog is
  open needs its Undo note inside the dialog. Found by testing a real-app
  mock-up (The Shortlist #60, Nov 2026).
- **A menu that closes on "click outside" also closes when your own code
  clicks a hidden button** (e.g. a menu item that works by calling
  `someButton.click()`): that click bubbles to `document` from outside the
  menu. Only close on real clicks: `if (e.isTrusted && !e.target.closest('.menu')) close()`.
  (Edit 1 Job Board, Nov 2026: the theme choice shut the profile menu.)
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
  user in The Shortlist's edit-sheet mock-up.)

## Wording

- **Hint text in a box (placeholder): measure the room before writing it.**
  A box with a button or label inside it (padding reserved on one side) fits
  far fewer letters than it looks: about 15 on a 375px phone with 100px
  reserved, about 22 without. Measure each line against the box's inner
  width (canvas `measureText` with the input's font, at 375px and 320px),
  reserve the space only while the thing it's for is showing, and add
  `:placeholder-shown { text-overflow: ellipsis; }` so an over-long line
  ends in "…" rather than mid-letter. Keep the `aria-label` plain when the
  visible hint is playful. (test-app Issue #37, Nov 2026.)
- **Confirm dialogs:** ask about the action ("Biff this job?", not "Has this
  job been biffed?"), name the thing, say what happens and whether it can be
  undone, and label the buttons with the action ("Keep job" / "Biff job", never
  "No / Yes"). Put focus on the safe button, not the ✕. If the app has an Undo
  bar, don't ask at all by default; offer the question only as a setting.
  (Edit 1 Job Board, issue #13.)

- Plain, friendly, short. Say what the user can do or see.
- **Feedback and report receipts never promise action:** "We review every
  report. If it leads to a change in a future update, we'll let you know",
  not "we'll fix it". A follow-up says "it's now live", not "fixed" (it may
  be a tweak or a feature). Keep tool names (GitHub, issue trackers) out of
  what testers and end users see. (test-app "Report issue", Nov 2026.)
- Explain anything technical in brackets the first time.

## Rich-text boxes (contenteditable)

- **Set `document.execCommand("defaultParagraphSeparator", false, "p")`**
  when editing starts. Chrome otherwise makes each new line a `<div>`; if
  your save step only keeps an allow-list of tags, the lines lose their
  breaks and run together, and the next "make this a heading" turns the
  whole run into one heading. Also turn stray `<div>`s into `<p>` when
  saving, and repair content saved before the fix.
- **Pasted text often arrives wrapped in `<b style="font-weight:normal">`**
  (Google Docs and others). If you strip styles but keep `<b>`, everything
  pasted turns bold: unwrap those first.
- Test it the way people use it: type, format, save, **reopen and format
  again**; the bug only shows on the second edit. (Edit 1 Job Board #33,
  Nov 2026)
