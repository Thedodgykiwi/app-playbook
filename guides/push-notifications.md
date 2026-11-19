# Push notifications (reminders) for a web app, including iPhone

Last verified: Nov 2026 (The Shortlist #51: reminders at a to-do's time).

How to get notifications into the phone's Notification Centre from a plain
HTML/JS app on GitHub Pages, using the Firebase project the app already has.

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

## Design that avoids double reminders

**One reminder channel per device, decided by a setting, not by "is the app
open?"**: a device with phone notifications on gets only those; a device
without them (Safari tab, permission off, signed out) gets an in-app reminder
card while the app is open. Store the choice per stage on the device
(`push-on-<stage>`). Tag each notification with the item's id so a newer one
replaces it and the app can close it when the item is ticked off
(`registration.getNotifications({ tag })`).

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
   the worker controls the look): `showNotification(title, { body, tag, data })`;
   handle `notificationclick`: focus an open window and `postMessage` the item
   id, or `openWindow(url + '?todo=<id>')`.
5. **Server (`functions/`, Cloud Functions v2, region near the data, e.g.
   europe-west2):** a scheduled function every minute sends what fell due
   since its last run (store `lastRun`; cap the look-back, e.g. 30 min),
   computes local times **in the device's time zone** (Intl, handles summer
   time), records each send once (`create()` a doc keyed by device+item+time,
   skip if it exists; prune after a few days), and deletes device records whose
   token comes back `registration-token-not-registered`. Add a callable
   "send a test" function for the Settings screen.
6. **Deploy:** `npx -y firebase-tools@latest deploy --only firestore:rules,functions --project <id> --force --non-interactive`.

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
  rules first, then code.
