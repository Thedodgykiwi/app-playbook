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
- **Issue pills** at the end of a release note ("tweak #2"): small rounded
  pill in the GitHub label's colour, `.72rem` bold, text dark or white
  (whichever contrasts more with the colour), kept on the same line as the
  word before it (`white-space: nowrap` wrapper), **not a link**: it's a
  quiet reference that a reported issue was dealt with. Code:
  test-app's `whats-new.js` (`pill()`).

## Wording

- Plain, friendly, short. Say what the user can do or see.
- Explain anything technical in brackets the first time.
