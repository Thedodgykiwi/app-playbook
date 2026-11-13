# App screens with Preact (React-style, no build step)

The starter builds the app's own screens with **Preact + htm + Signals**:
React-style components that run straight in the browser. Chosen because the
starters grow into bigger apps: the screen follows the data (no hand-written
"find the row, update the counter" code), components are reusable, and the
patterns are React's, so moving to full React later is mostly mechanical.
The menu, sign-in, offline and install code stay plain JS.

## What's where

| Path | What it is |
|---|---|
| `vendor/` | The libraries, stored in the app (no CDN: works offline, fixed versions). Versions and licences in `vendor/README.md` |
| `<script type="importmap">` in `index.html` and `styleguide.html` | Lets code `import … from 'preact'` by name, like React code |
| `app/main.js` | The app's entry: renders `<App />` into `<main id="app">` |
| `app/example.js` | **Starter example** (add / tick / filter / delete, empty state). Delete it and its import when building |
| `styleguide-components.js` | Live examples in the style guide's "Components (Preact)" section, with their code |

## Patterns (see the style guide for working examples)

```js
import { html, render } from 'htm/preact';
import { useState, useEffect, useRef } from 'preact/hooks';
import { signal, computed } from '@preact/signals';

// Local state (only this component needs it)
const [text, setText] = useState('');
// Shared data (any component reading it re-draws when it changes)
const items = signal([]);                        // read/write: items.value
const left = computed(() => items.value.filter((i) => !i.done).length);
// Markup: htm tagged templates instead of JSX
html`<${Item} key=${i.id} item=${i} onDone=${() => toggle(i.id)} />`
```

- **Change arrays/objects by replacing them** (`items.value = [...items.value, x]`),
  not by pushing into them, so signals notice.
- **Lists need a `key`** (a stable id) on each item.
- **Use the style kit's classes** (`btn`, `input`, `card`, `list`…) and
  `icon('name')` (Phosphor Regular). In components: `<${Icon} name="plus" />`
  (see `app/example.js`).
- Keep **saving** (browser storage per app + stage, or the account via
  `account.js`) in plain functions next to the signals, not inside components.
- htm differences from JSX: `${…}` for every value, `<${Component}>` for
  components, `class` (not `className`) works, `...${props}` to spread.

## Offline

Modules imported by name aren't linked from the HTML, so the deploy's `?v=`
stamping doesn't reach them. They're fetched network-first (always fresh when
online), and `pwa.js` tells the service worker every file the page loaded, so
they're saved for offline too.

## Updating a library

`npm pack <name>@<version>`, copy the same file(s) into `vendor/`, remove the
trailing `sourceMappingURL` comment (the files are one line: don't delete the
line!), update the table in `vendor/README.md` and the licence in
`LICENSES/`. Test the example, the style guide and offline mode.

## When to move to full React (with a build step)

When an app needs React-only libraries (e.g. shadcn/ui, complex data grids),
TypeScript everywhere, or a team that expects a standard React project. The
components carry over: swap `html\`…\`` for JSX, `preact` for `react`.

## Moving an existing plain-JS screen to Preact (done in test-app, Nov 2026)

1. **Split data from screen first:** move the list, loading flag and saving
   into a `store.js` of signals with the *same* storage keys, data format and
   hooks other code uses (test-app's `window.TodoApp` for `sync.js`). Replace
   arrays/objects instead of changing them in place.
2. Rebuild the screen as components reading those signals; keep ids and
   classes the CSS and tests use.
3. **Load order:** module scripts run in page order, so put the store's module
   before any module that needs its hooks (`app/main.js` before `sync.js`).
4. **Keyboard focus:** a ticked row moves to another list, so its element is
   new: remember a selector and focus it in an effect after the next draw.
   Don't give a button a changing `key` to replay an animation (it remounts and
   loses focus); restart the CSS animation with a class instead.
5. **Animations that end in a save:** look the item up again by its key when
   the animation finishes; don't save the object you had when it started. The
   list can be re-read meanwhile (test-app: sign-in finishing just after the
   page opens replaced every to-do, so a tick made in that moment was lost).
6. Re-test with **old saved data**, signed in (emulators), keyboard, offline.
