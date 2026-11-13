# Firebase: Google sign-in and a cloud database

How to add "Sign in with Google" and save each user's data in the cloud
(Cloud Firestore) to a plain HTML/CSS/JS app with no build step, hosted on
GitHub Pages. Worked example: `Thedodgykiwi/test-app` (to-do list that
saves to the device when signed out and to the user's account when signed in).

Last verified: November 2026, firebase-tools latest, Firebase JS SDK 13.1.0.

---

## What you'll end up with

- A **Sign in** button. Signed out, the app works exactly as before (data
  on the device only). Signed in, data lives in the user's own folder in
  Firestore and follows them to other devices.
- On first sign-in on a device, that device's data is **copied** into the
  account (the device copy is left alone).
- Works offline once loaded; changes sync when the connection returns.
- **Security rules** that let each person read and change only their own
  data, with every field checked, plus automated tests for those rules.
- Everything free (Spark plan, Firestore free tier).

## Before you start (ask the user)

1. **Firebase project.** The user creates it in the Firebase console
   (console.firebase.google.com → Add project). Google Analytics: off
   unless they want it. Note the **project ID** (e.g. `my-app-12345`).
2. **Which Google account** owns the project. Claude signs in to Firebase
   as that account (step 1 below).
3. **Firestore location.** Ask: it **can't be changed later**. Common picks:
   `australia-southeast1` (Sydney: NZ/AU), `nam5` (US), `eur3` (Europe).
4. Whether they want a **concept mock-up** of where sign-in goes in the UI
   (it's a visible change; see "Concept first" in `working-with-the-user.md`).

## Order of work

Do it in this order; each step depends on the one before.

### 0. Cloud session network (Claude Code on the web)

A cloud session's network blocks Firebase by default. The user's
**Default** environment should already allow these hosts (they chose to
allow Firebase for all apps, since most will use it). If a session is on an
environment that doesn't, ask to add them (see `cloud-sessions.md`).

```
auth.firebase.tools             # Firebase CLI / MCP sign-in
accounts.google.com
oauth2.googleapis.com
www.googleapis.com
firebase.googleapis.com
firestore.googleapis.com
firebaserules.googleapis.com
identitytoolkit.googleapis.com  # Auth settings, authorised domains
securetoken.googleapis.com
cloudresourcemanager.googleapis.com
serviceusage.googleapis.com
apikeys.googleapis.com
iap.googleapis.com
www.gstatic.com                 # Firebase JS SDK (the app loads it from here)
apis.google.com                 # needed for the sign-in POP-UP, even with emulators
storage.googleapis.com          # emulator downloads
<username>.github.io            # so Claude can check the live site after deploys
```

`apis.google.com` and `<username>.github.io` were the two we missed the
first time. The sign-in pop-up on the **live** site also loads
`<project-id>.firebaseapp.com`; it isn't needed, because a real Google sign-in
can't be completed from a cloud session anyway (the user tests that). Without `apis.google.com`, `signInWithPopup` fails with
`auth/internal-error` even against the local emulator.

### 1. Sign Claude in to Firebase

Use the **Firebase plugin's MCP tools** (`mcp__plugin_firebase_firebase__*`;
load them with ToolSearch "firebase" once the server has connected). Also use
Firebase's official agent skills (github.com/firebase/agent-skills) if the
session has them.

- `firebase_get_environment` shows the active project and whether anyone is signed in.
- `firebase_login` (no arguments) returns a URL **and a session ID**. Show
  the user **both**, and tell them to check the session ID on the page
  matches before allowing access (anti-phishing). They paste back an
  authorisation code; call `firebase_login` again with `authCode`.
- Check access with `firebase_get_project`.

The sign-in lasts for the cloud session only. The token is stored in
`~/.config/configstore/firebase-tools.json`, which is useful for REST calls the
MCP tools don't cover (step 5).

### 2. Register the web app → `firebase-config.js`

- `firebase_create_app` (platform `web`, display name e.g. "My App (web)").
- `firebase_get_sdk_config` with the returned app ID.
- Put the values in `firebase-config.js` (template in `templates/firebase/`).
  These values are **not secret**: every Firebase web app ships them to the
  browser. Security comes from the rules.
- **Leave out `measurementId`.** It's only for Google Analytics, and adding
  tracking needs the user's OK.

### 3. Create the Firestore database

`firestore_create_database` with:
`databaseId: "(default)"`, `locationId: <user's choice>`,
`type: FIRESTORE_NATIVE`, `databaseEdition: STANDARD`,
`deleteProtectionState: DELETE_PROTECTION_ENABLED`.
Check the response says `"freeTier": true` (only one database per project
gets the free tier).

### 4. Turn on Google sign-in

`firebase_init` with
`features.auth.providers.googleSignIn = { oAuthBrandDisplayName, supportEmail }`,
then `firebase_deploy` with `only: "auth"`.

> ⚠️ **Gotcha: email in a public repo.** `firebase_init` writes the support
> email into `firebase.json` (and adds empty `targets`/`etags` to
> `.firebaserc`). Deploy, check it's done, then **`git checkout firebase.json
> .firebaserc`** so the email never gets committed. Deploys run in the
> background: poll `firebase_deploy_status` with the job ID.

The support email must belong to the account Claude signed in as (or a
group it owns). It appears on Google's consent screen.

### 5. Allow the website's address (authorised domains)

Sign-in only works on web addresses on the project's **authorised domains**
list. The MCP tools can't edit it, so use the Identity Toolkit admin API with
the CLI's token:

```bash
TOK=$(python3 -c "import json;print(json.load(open('/root/.config/configstore/firebase-tools.json'))['tokens']['access_token'])")
P=YOUR-PROJECT-ID
# read
curl -sS -H "Authorization: Bearer $TOK" -H "x-goog-user-project: $P" \
  https://identitytoolkit.googleapis.com/admin/v2/projects/$P/config | grep -A6 authorizedDomains
# write (send the WHOLE list: it replaces the old one)
curl -sS -X PATCH -H "Authorization: Bearer $TOK" -H "x-goog-user-project: $P" -H "Content-Type: application/json" \
  "https://identitytoolkit.googleapis.com/admin/v2/projects/$P/config?updateMask=authorizedDomains" \
  -d '{"authorizedDomains":["localhost","'$P'.firebaseapp.com","'$P'.web.app","<username>.github.io"]}'
```

- GitHub Pages: add the **host only** (`<username>.github.io`), no path.
  That one entry covers every stage (`/app/`, `/app/dev/`, …).
- Add `localhost` (new projects may not have it) so local previews can sign in.
- Confirm Google is on: GET `.../defaultSupportedIdpConfigs` should list `google.com True`.
- Symptom if missing: sign-in shows `auth/unauthorized-domain`.

### 6. Security rules: write, test, deploy

Start from `templates/firebase/firestore.rules`. Principles:

- **Owner only:** `request.auth.uid == userId` on every path.
- **Deny by default.** Only match the exact paths the app uses.
- **Validate every field:** required (`keys().hasAll`), nothing extra
  (`keys().hasOnly`), types, lengths, allowed values.
- **Server time:** `createdAt == request.time` on create (the app sends
  `serverTimestamp()`), so clients can't fake it.
- **Immutable fields:** on update, `diff(resource.data).affectedKeys().hasOnly([...])`.
- **No delete until the app has a delete feature.** Add it when needed.
- **Whitelist stage names** in the path (see "Stages" below).

Then:

1. `firebase_validate_security_rules` (catches syntax errors).
2. Run the tests: `npm install` then `npm run test:rules` (template in
   `templates/firebase/tests/`, `package.json` script uses
   `firebase emulators:exec` with a `demo-` project, so it never touches the
   real project). Needs Java (present in cloud sessions).
3. **Prove the tests bite:** temporarily loosen a rule (e.g. `allow delete:
   if true;`), check a test fails, then `git checkout firestore.rules`.
4. Deploy: `firebase_deploy` with `only: "firestore"` (or
   `npx -y firebase-tools@latest deploy --only firestore:rules`).

Update the tests whenever the data model changes.

### 7. App code

Use `templates/firebase/sync.js` as the starting point (it's the to-do
version; rename collections/fields for your app). Key decisions in it:

- **SDK as ES modules from gstatic, pinned** (`firebasejs/13.1.0/...`). No
  npm or build step needed for the app. Update the version deliberately.
- **App works with `FIREBASE_CONFIG = null`**, so the code can ship before
  setup is done; sign-in UI stays hidden.
- **If the SDK fails to load** (offline first visit), fall back to local
  storage quietly.
- **Offline:** `initializeFirestore(app, { localCache: persistentLocalCache({ tabManager: persistentMultipleTabManager() }) })`.
- **Live sync:** `onSnapshot(query(..., orderBy('pos')), { includeMetadataChanges: true }, ...)`;
  `snap.metadata.hasPendingWrites` → "Saving…" status.
- **First sign-in copy:** only after a snapshot with `fromCache === false`
  (so you know what's already in the account); skip duplicates; batches
  of ≤ 500 writes; remember with a per-stage, per-user flag in
  localStorage; **never delete** the device copy.
- **Friendly errors** for `auth/popup-blocked`, `auth/network-request-failed`,
  `auth/unauthorized-domain`; ignore `auth/popup-closed-by-user`.
- The main app exposes small hooks (`useLocal`, `useCloud`, `setTodos`,
  `localTodos`, `stage`) so `sync.js` stays separate from the UI code.
- Emulator switch: `http://localhost:8080/?emulators` connects to the local
  Auth (9099) and Firestore (8081) emulators.

### 8. Test end to end (before pushing)

```bash
npx -y firebase-tools@latest emulators:start --only auth,firestore --project demo-my-app   # background
python3 -m http.server 8080                                                               # background
```

Then drive `http://localhost:8080/?emulators` with Playwright. The
emulator's fake Google pop-up:

```js
const [popup] = await Promise.all([ctx.waitForEvent('page'), page.click('#sign-in')]);
await popup.waitForLoadState();
await popup.getByText('Add new account').click();
await popup.locator('#email-input').fill('tester@example.com');
await popup.locator('#display-name-input').fill('Test User');
await popup.locator('#sign-in').click();   // the pop-up's own button
```

(The "Auto-generate user information" button didn't work reliably; fill
the fields instead. The pop-up looks unstyled in cloud sessions because its
fonts are blocked. That's fine.)

Check: signed-out features unchanged and persist after reload; sign-in
copies device data; add/edit while signed in shows "saved", survives a
reload; sign-out returns to the device list; phone width (375 px); no
console errors. A 404 for files the deploy generates (e.g. `releases.json`)
is expected locally.

**What can't be tested from a cloud session:** a real Google sign-in. The
user does that on the Dev site; tell them so honestly.

### 9. Push, deploy, hand over

Commit `firebase-config.js` (+ rules, tests) to `dev`, confirm the Pages
deploy succeeded, then ask the user to sign in on the Dev URL. Record what
was set up (app ID, location, domains) in the app's CLAUDE.md, but **no
personal email addresses**.

---

## Stages share one sign-in

All GitHub Pages stages live on one web address (`<username>.github.io`), so:

- **Sign-in is shared**: signed in on Dev = signed in on Production in the
  same browser.
- **localStorage is shared** too: key everything per stage
  (`todos-<stage>`, `copied-<stage>-<uid>`).
- **Keep data separate per stage in Firestore:**
  `users/{uid}/stages/{stage}/...`, with stage names whitelisted in the
  rules. Otherwise testing on Dev changes real Production data.

## Adding a field to stored data (e.g. a "done at" time)

Strict rules (`keys().hasOnly([...])`) reject any new field, so signed-in
saves would fail if the app ships first. Order (done this way on test-app):

1. Make the field **optional** in the rules (allow absent/null, validate type
   and range) and add it to `onlyChanges([...])` if it changes on update.
2. Add rules tests for it (valid, null, wrong type, out of range, other
   user), run them, and loosen the rule once to prove they fail.
3. Test the app against the emulators **signed in** (save, reload, it comes
   back).
4. **Deploy the rules first**, check them live (`firebase_get_security_rules`),
   then push the app change. Old app versions keep working with the new rules.
5. Existing records without the field: handle "missing" in the app (e.g. show
   under "Older") rather than inventing values.

## Gotchas (quick list)

- Network: `apis.google.com` is needed for the sign-in pop-up; `<username>.github.io` to check the live site.
- `firebase_init` auth writes the support email into `firebase.json`; revert after deploying.
- Authorised domains aren't in the MCP tools; use the REST call above. Host only, no path.
- Firestore location is permanent; ask first. Turn on delete protection.
- `measurementId` = Analytics; leave it out unless the user wants tracking.
- `firebase_deploy` is asynchronous; poll `firebase_deploy_status`.
- **Edits must target the current record, not a captured copy.** Lists get
  re-read (sign-in check after load, live updates from other devices), which
  replaces the objects in memory. An editor that keeps a reference to "the
  to-do being edited" will save to a stale copy and lose the change: look it
  up again by id when saving.
- The emulator's fake sign-in pop-up is sometimes slow to finish in cloud
  sessions: in Playwright, poll for the signed-in state for up to a minute
  instead of a single short wait, and retry once before suspecting the app.
- In a new session the Firebase sign-in may still be valid, but there's no
  active project: `firebase_deploy` fails with "requires an active project".
  Call `firebase_update_environment` with `project_dir` (the app repo) and
  `active_project` first.
- Emulator project IDs must start with `demo-` so nothing reaches the real project.
- `[hidden]` can be overridden by CSS `display`; add `[hidden] { display: none !important; }`.
- Never delete users' device or cloud data without asking; migrate formats instead.
- Billing stays off (Spark). Anything that needs Blaze (Cloud Functions, etc.) needs the user's OK.
