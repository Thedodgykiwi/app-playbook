# Push notifications (reminders) for a web app, including iPhone

Last verified: 19 Nov 2026 (The Shortlist #51: reminders at a to-do's time, tested on an iPhone).

How to get notifications into the phone's Notification Centre from a plain
HTML/JS app on GitHub Pages, using the Firebase project the app already has.
**Worked example:** `Thedodgykiwi/test-app` (reminders, Issue #51); the code to
copy is listed at the end. Built in this order: in-app reminders first (no
billing, works everywhere), then phone notifications on top.

## What's possible (say this to the user first)

- **iPhone:** only for the app **added to the Home Screen** (iOS 16.4+). A
  Safari tab can't receive them. Each stage added to the Home Screen is a
  separate app with its own permission.
- **Permission must be asked inside a tap** (e.g. a "Turn on phone
  notifications" button). iOS ignores a prompt that pops up on its own.
- **Every push must show a notification** on iPhone; if pushes arrive and
  nothing is shown, iOS turns the app's notifications off. So the app can't
  "stay quiet because it's open".
- **No buttons** on iPhone web notifications: a tap opens the app; put Done /
  Snooze in the app.
- **iOS adds a "from <app name>" line** between the title and the body (the
  Home Screen app's short name, e.g. "from Shortlist Dev"). It can't be hidden
  or moved; keep titles short so the three lines stay compact, and remember the
  test stages show their stage word there.

## Design that avoids double reminders

**One reminder channel per device, decided by a setting, not by "is the app
open?"**: a device with phone notifications on gets only those; a device
without them (Safari tab, permission off, signed out) gets an in-app reminder
card while the app is open. Store the choice per stage on the device
(`push-on-<stage>`). Tag each notification with the item's id so a newer one
replaces it and the app can close it when the item is ticked off
(`registration.getNotifications({ tag })`).

## What the user sees (the pattern that worked)

- **Settings → Reminders:** a default ("Remind me: at the time / 15 min / 1
  hour before") and a **Phone notifications** part whose text changes with the
  state: not supported · iPhone Safari tab ("add it to your Home Screen and open
  it from there") · signed out ("sign in to get notifications") · blocked
  ("Settings → Notifications → <app>") · off ("Turn on phone notifications") ·
  on ("Send a test notification", "Turn off on this device").
- **Each item:** its own choice (Off / at the time / 15 min / 1 hour). Store
  only overrides: `remind` null = follow the default, so changing the default
  moves every item that never chose. Items with a reminder show a small bell.
- **The in-app card** (devices without phone notifications, and every tap on a
  notification): the item, "Due in 15 min · 4pm", **Done / 10 min (snooze) /
  Date**, ✕, and the name opens the edit panel. Put it in a `popover`
  (`showPopover()`, top layer) so it shows above open modal dialogs. Show each
  reminder once (remember what was shown or snoozed per stage on the device,
  prune after a few days); check every ~20 s and on `visibilitychange`.
- **Snooze** keeps the item's own time and saves a separate `snooze` time on
  the item (so the server and other devices remind again); show it on the row
  ("🔔 4:10pm") with Cancel in the edit panel; a new date or time clears it.
- **Expect up to about a minute's delay** (an every-minute sender plus Apple's
  delivery); tell the user before they test.

## The pieces

| Piece | What | Cost |
|---|---|---|
| **Firebase Cloud Messaging (FCM)** | Delivers to the browser / Apple | Free |
| **A sender** | Something that decides *when* to send | See below |
| **Your service worker** | Shows the push, opens the app on tap | — |

Sender options: a **scheduled Cloud Function** (on time; needs the **Blaze**
plan, i.e. a card on file; at small-app scale it's £0, set a £1 budget alert),
or the free **GitHub Actions** scheduled job (no billing, but GitHub runs
schedules 5–15 minutes late). Third-party services (OneSignal etc.) add an
account and a data processor for no real gain if Firebase is already in use.

## Steps

1. **User, in the Firebase console:** upgrade to Blaze and set a budget
   alert; then Project settings → Cloud Messaging → Web configuration → Web
   Push certificates → **Generate key pair** and give Claude the key (it's the
   public half: it goes in `firebase-config.js` as `window.FIREBASE_VAPID_KEY`).
2. **Rules + tests first**: a per-device record
   `users/{uid}/devices/{id}` = `{ token, stage, lead, tz, url, updatedAt }`,
   owner-only, every field checked; the server's own bookkeeping
   (`system/…`) has no client access. Run the rules tests, deploy rules
   **before** pushing app code that writes the new data (otherwise signed-in
   writes are refused; keep the code on a `wip/` branch until then).
3. **App (sync.js):** on the button, call `Notification.requestPermission()`
   **first, synchronously in the click handler**, then import
   `firebase-messaging.js` from gstatic, `getToken(messaging, { vapidKey,
   serviceWorkerRegistration: await navigator.serviceWorker.ready })` (use the
   app's own worker, not `firebase-messaging-sw.js`), save the device record.
   Refresh the token on each signed-in open; delete the record on sign-out,
   "turn off" and account deletion; include it (token shortened) in "Download
   my data"; mention it on the privacy page.
4. **Service worker:** handle `push` yourself (send **data-only** messages, so
   the worker controls the look; FCM wraps it, so read `json.data || json`):
   `showNotification(title, { body, tag, data })`; handle `notificationclick`
   (see the gotcha below: note the tap first, `postMessage`, then try
   `focus()`, else `openWindow(url + '?todo=<id>')`). Each stage has its own
   worker; Production's scope contains the test stages' folders, so skip
   windows from `/dev/`, `/alpha/`, `/staging/` when matching.
   Bookkeeping in the repo: `firebase.json` gets a `functions` entry (source
   `functions`, runtime `nodejs22`), `functions/node_modules/` goes in
   `.gitignore`, `functions/package-lock.json` is committed.
5. **Server (`functions/`, Cloud Functions v2, region near the data, e.g.
   europe-west2):** a scheduled function every minute sends what fell due
   since its last run (store `lastRun`; cap the look-back, e.g. 30 min),
   computes local times **in the device's time zone** (Intl, handles summer
   time), records each send once (`create()` a doc keyed by device+item+time,
   skip if it exists; prune after a few days), and deletes device records whose
   token comes back `registration-token-not-registered`. Add a callable
   "send a test" function for the Settings screen.
6. **Deploy:** Claude needs a Firebase sign-in in the session
   (`firebase-auth-and-firestore.md` step 1), then
   `npx -y firebase-tools@latest deploy --only firestore:rules,functions --project <id> --force --non-interactive`
   (`--force` also sets the container-image clean-up policy; without one,
   old images slowly build up a small bill).
7. **Test on the phone** (Claude can't): add the stage to the Home Screen,
   open it from there, sign in, Turn on → Allow, **Send a test notification**;
   then an item with a time ~20 minutes ahead, app **closed**, tap the
   notification; repeat with the app **in the background**; try Snooze.
   Headless, Claude can still test the rules, the time-zone maths, the card
   (open `?todo=<id>`) and the "tap noted while in the background" path (write
   the note into the worker's cache, fire `visibilitychange`).

## Server code and rules are not staged

The Cloud Functions and the security rules live in the **one Firebase project
every stage uses**, so a deploy is live for Dev, Alpha, Staging **and
Production at once**, whatever branch the app code is on. So: keep server and
rules changes **backwards compatible** (old app versions on other stages keep
working: new fields optional, nothing removed), deploy them **before** the app
code that needs them, and say in the release notes that the server side was
already live. Promotions only move the app code.

## Cost (small app)

An every-minute schedule is about 43,000 runs a month: inside Cloud Functions'
free allowance, and Cloud Scheduler's 3 free jobs. Each run reads a few
documents. Expected bill £0; the £1 budget alert is the safety net.

## A daily summary (once a day, at a chosen time)

Same sender, same device record: add optional `sumOn / sumTime / sumDays /
sumSkip` to the device, and in the every-minute run send it when the
device's chosen time (in its time zone) falls since the last run; log it as
sent once per local day. Wording that worked on the Lock Screen: title
"☀️ Today: 5 to do", body one line each, overdue first ("⚠️ … (overdue)",
"⏰ 9:30am …", "🌙 …", "• …"), at most 3 lines + "+2 more" (titles: keep to
about 30 characters with an emoji, or a narrower iPhone cuts them off; body
~150 characters before "more"; emoji display fine). Offer
"Skip days with nothing due" (on by default) and a "Send me today's summary
now" button (a callable function) for testing. Tapping it should open the
overview (e.g. All to-dos), carried as a `view` in the push. (The Shortlist #91.)

## A bit of personality

Each kind of notification can pick a random line from a small set (an
app-specific `LINES` list on the server, like the add box's hint lines): the
**joke goes in the title only**; the item's name and time stay plain in the
body ("Call the venue · 4pm (in 15 min)"). Draft the lines as rendered
notification previews for the user to approve, check none get cut off at
375px, and handle singulars ("1 nominee"). It's server-only wording: changing
it is a functions deploy, live on every stage at once. (The Shortlist #92.)

## Where a tap on the notification lands

Open an **action card** for that item (Done / Snooze / Change date, with the
item's name opening the full edit panel), not the edit panel itself: an edit
panel's "Done" (= close) reads as "mark it done". Save **Snooze** on the item
(e.g. `snooze: <ms>`), not just on the device, so the server can send a fresh
notification and other devices remind again too. (The Shortlist #51, Nov 2026.)

## Gotchas

- **First functions deploy enables several Google Cloud services**; one
  function can fail with "Could not create bucket" / "missing permissions".
  Re-run the deploy for that function a minute later; it works.
- Check the schedule really runs: Cloud Scheduler's job shows
  `lastAttemptTime` (REST: `cloudscheduler.googleapis.com/v1/projects/<id>/locations/<region>/jobs`
  with the CLI's token) and the function's `lastRun` doc updates each minute.
  "Request was not authenticated" log lines right after a deploy are health
  checks, not the scheduler.
- **A tap while the app is open in the background can get lost on iPhone:**
  `WindowClient.focus()` may be refused, and code after it (e.g. `postMessage`)
  never runs. Note the tapped item first (e.g. in the worker's cache), post the
  message before focusing, wrap `focus()` in try/catch, and have the app check
  for the note on load and on `visibilitychange`. (The Shortlist #51.)
- Pushing to `dev` before the rules are deployed would break signed-in saves:
  rules first, then code. If the session can't deploy yet (no Firebase
  sign-in), push the work to a `wip/` branch, not `dev`.

## Code to copy (from the worked example, `Thedodgykiwi/test-app`)

| What | Where |
|---|---|
| Settings section (Reminders, Phone notifications) | `index.html` (`#st-reminders`, `#push-setting`) |
| Turn on / off, token, device record, test button, states | `sync.js` ("Phone notifications" section) |
| Per-item reminder, in-app card, snooze, tap handling | `app/main.js` (`remOf`, `RemindCard`, `remCheck`, `openWantedTodo`, `checkTapped`) |
| Showing pushes, tap → app | `sw.js` (end: `push`, `notificationclick`) |
| Sender + test function | `functions/index.js` (`sendReminders`, `sendTestReminder`, `zonedMs`) |
| Rules and tests | `firestore.rules` (`isValidDevice`, `remind`, `snooze`), `tests/firestore.rules.test.mjs` |

These are app-owned (they depend on the app's data), so copy and adapt them
rather than linking; rename `todo` to the app's item. Privacy page: say what's
stored for notifications (device code, time zone, default time) and that
Google delivers them (Apple for iPhone).
