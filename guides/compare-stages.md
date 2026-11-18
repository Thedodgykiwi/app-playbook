# Comparing stages side by side

Last verified: Nov 2026 (The Shortlist, Issue #69)

Every app gets this from the **shared deploy**; there's nothing to copy into
the app. It has three parts:

1. **Pipeline page → Compare tab.** The Pipeline page (`<app>/pipeline/`) has
   two tabs: **Pipeline** (as before) and **Compare**. Compare shows every
   stage in a phone-sized window, side by side on a computer and as stage tabs
   on a phone, with one Light / Dark switch for all of them and **Reset sample**.
   The windows only load when Compare is opened; the page remembers the tab.
2. **Compare mode** (`?compare` on any stage's address). Every stage reads and
   writes **one shared set of data in this browser** instead of its own, so all
   stages show exactly the same content and only the design differs. Add, edit
   or tick in any window and the others update. Sign-in and cloud sync are off,
   so nothing reaches an account; the stages' own lists are never touched.
   The banner says "<Stage> · compare" with a **Reset** button (Production gets
   a banner in its own colour while comparing).
3. **Stage switcher.** On Dev, Alpha and Staging, tapping the banner's stage
   name opens a menu (Dev · Alpha · Staging · Production) that goes to the same
   app on another stage, keeping compare mode on if it's on. Production has no
   banner in normal use, so nothing changes there.

## How it works (for Claude)

- The deploy copies `.github/scripts/compare.js` into every stage (with the
  stage colours filled in) and adds `<script src="compare.js">` right after
  `stage.js`. In normal mode it only adds the banner switcher.
- In compare mode it remaps storage keys ending in `-<stage>` or `:<stage>`
  (the starter's convention, e.g. `todos-dev`) to `-compare` / `:compare`,
  blocks `signed-in` and `cloud-copy-*`, and makes `window.FIREBASE_CONFIG`
  always `null`. Apps that key their data per stage need no changes.
- `window.COMPARE` is `true` in compare mode: use it to skip one-time tips or
  anything that shouldn't appear while comparing.

## The app's part: `compare-sample.json` (optional, recommended)

In the app's root, on `dev`:

```json
{ "key": "todos", "items": [ { "text": "Call the venue", "due": "@today", "doneAt": "@now-2h" } ] }
```

- `key` is the app's data key without the stage (the app saves `todos-dev`,
  so `"todos"`). `items` is the starting data, in the app's own format.
- Relative dates so the sample never goes stale: `"@today"`, `"@today+1"`,
  `"@today-2"` (a `YYYY-MM-DD` date); `"@now"`, `"@now-2h"`, `"@now-3d"` (a
  timestamp in milliseconds).
- Include one example of every feature you want to compare (starred, overdue,
  timed, checklist, note, done…). Keep it short: 6–10 items.
- The deploy copies **Dev's** sample to every stage, so older stages start
  from the same list. Older stages simply don't show features they don't
  have yet, which is the point.
- No sample file: compare mode still works, starting from an empty shared list.

## Gotchas

- **Only react to the data key.** Apps write small housekeeping values on
  every load (which hint line was shown, visit counters); reloading other
  windows on those caused an endless reload loop. compare.js only reloads
  windows when the sample's list really changes.
- Compare data is per browser, per device. It isn't synced.
- An app that doesn't key its data per stage (`-<stage>` / `:<stage>`) won't
  be separated in compare mode: rename its keys to the convention first.
