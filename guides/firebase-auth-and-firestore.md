# Firebase: Google sign-in and a cloud database

How to add "Sign in with Google" and save each user's data in the cloud
(Cloud Firestore) to a plain HTML/CSS/JS app with no build step, hosted on
GitHub Pages. Worked example: `Thedodgykiwi/test-app` (to-do list that
saves to the device when signed out and to the user's account when signed in).

Last verified: 18 November 2026, firebase-tools latest, Firebase JS SDK 13.1.0 (rules deployed and tested with the emulators).

---

## What you'll end up with

- **Sign in with Google** at the top of the menu (signed out). Signed out, the app works exactly as before (data
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

The sign-in lasts for the cloud session only, and the login link dies if
the MCP server restarts (call `firebase_login` again for a fresh one). The
token is stored in `~/.config/configstore/firebase-tools.json`, which is
useful for REST calls the MCP tools don't cover (step 5).

### 1b. Point the tools at THIS app's project first

Before any other Firebase tool, add `.firebaserc` (`{"projects":{"default":"<project-id>"}}`)
and `firebase.json` (template) to the app's repo, then
`firebase_update_environment` (project_dir + active_project) and **check
`firebase_get_environment` shows the right Active Project ID**. Without a
`firebase.json` the tools silently keep the *previous* app's project, so
`firebase_create_app` registered a web app in the wrong project (found on
the second app). If that happens, remove it in that project's console:
Project settings → Your apps → the app → Remove this app.
In a later session the sign-in may still be valid but with no active
project (`firebase_deploy` fails with "requires an active project"): call
`firebase_update_environment` again first.

**New project made by Claude (`firebase_create_project`):** the Cloud
Firestore API starts switched off (Firebase's own docs: adding Firebase does
not enable `firestore.googleapis.com`), so `firestore_create_database` fails
with "API has not been used". The Firebase MCP has no tool to enable APIs.

**Approved way (the user agreed to this, 2026-11-13):** Claude enables it with
the Service Usage API using the Firebase CLI's sign-in. Ask the user in the
moment first, in one line ("OK to switch on Firestore for <project>?"): their
"yes" in that session is what lets the call through Claude Code's safety
check. Then:

```bash
TOK=$(python3 -c "import json;print(json.load(open('/root/.config/configstore/firebase-tools.json'))['tokens']['access_token'])")
P=YOUR-PROJECT-ID
curl -sS -X POST -H "Authorization: Bearer $TOK" -H "x-goog-user-project: $P" \
  https://serviceusage.googleapis.com/v1/projects/$P/services/firestore.googleapis.com:enable
```

Wait a minute, then retry `firestore_create_database`. (If the token has
expired, call any Firebase MCP tool first; it refreshes the file.)
Fallback if that's refused: the user creates the database in the console
(Build → Firestore Database → Create database: Standard, location, start in
production mode), or opens the "enable it" link from the error.

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
- **Owners may delete their own data** (needed for "Delete my account"); nobody else may.
- **Whitelist stage names** in the path (see "Stages" below).
- **Fixed choices as lists:** `data.color in ['red', 'orange', …]` for
  anything picked from a set (colours, icons, priorities); ids that point at
  other documents checked as short ids (`matches('^[A-Za-z0-9_-]{1,40}$')`).

Then:

1. `firebase_validate_security_rules` (catches syntax errors).
2. Run the tests: `npm install` then `npm run test:rules` (template in
   `templates/firebase/tests/`, `package.json` script uses
   `firebase emulators:exec` with a `demo-` project, so it never touches the
   real project). Needs Java (present in cloud sessions).
3. **Prove the tests bite:** temporarily loosen a rule (e.g. `allow delete:
   if true;`), check a test fails, then `git checkout firestore.rules`.
4. Deploy with the CLI: `npx -y firebase-tools@latest deploy --only
   firestore:rules --project YOUR-PROJECT-ID` (from the app repo's root).
5. **Check it's live:** `firebase_get_security_rules` (type `firestore`)
   must show the new rule, and its text must name the right app (it has
   shown another project's rules after switching). Why: the MCP
   `firebase_deploy` tool has reported "success" without releasing anything
   (twice, Nov 2026); the CLI above works with the same sign-in. A
   "permission denied" right after a rules change usually means the old
   rules are still live.

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
- **Don't hide the list until Firebase is ready.** For a returning signed-in
  user, `onAuthStateChanged` only fires after the SDK has downloaded (~1 MB)
  *and* Auth has checked the saved sign-in with Google over the network
  (token refresh + account lookup, every load), and Firestore can't read its
  own offline cache until then either. So an app that shows "Loading…" until
  the first snapshot pauses on every open, however few items there are.
  Keep a copy of the last list shown in localStorage, show it at once, and
  swap in the live list when it arrives (block edits until then). Measure
  it with Playwright before guessing. (The Shortlist #36, Nov 2026.)
- **Edits target the current record, not a captured copy.** Lists get
  re-read (sign-in check after load, live updates from other devices), which
  replaces the objects in memory; an editor holding "the item being edited"
  saves to a stale copy. Look it up again by id when saving.
- **Related collections** (e.g. lists that to-dos belong to,
  `users/{uid}/stages/{stage}/lists/{id}`): make the id on the device and
  save with `setDoc(doc(ref, id), …)`, so an item can point at a new one at
  once, before the server answers. On first sign-in copy them **before** the
  items, reuse one with the same name already in the account, and map the
  items' ids to it. (The Shortlist #72.)
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

(Filling the fields is the most reliable; "Auto-generate user information"
has worked too. The pop-up looks unstyled in cloud sessions because its
fonts are blocked. That's fine. It's sometimes slow: poll for the signed-in
state for up to a minute instead of one short wait. If the pop-up can't load
its scripts at all (it needs `unpkg.com`), sign in from the test instead with
an unsigned Google token only the Auth emulator accepts:
`await page.evaluate(async () => { const a = await import('https://www.gstatic.com/firebasejs/<version>/firebase-auth.js'); await a.signInWithCredential(a.getAuth(), a.GoogleAuthProvider.credential(JSON.stringify({ sub: 'u' + Date.now(), email: 'u' + Date.now() + '@example.com', email_verified: true }))); })`.
Use a new email each run: the emulator keeps users between runs.)

**Emulator project ID vs. the app's config:** emulator project IDs must
start with `demo-` (so nothing reaches the real project), while the app's
`firebase-config.js` has the real ID. With `firebase.json`'s
`"singleProjectMode": true` the app's own config works against the
emulators; otherwise serve a demo config in Playwright:
`ctx.route('**/firebase-config.js', r => r.fulfill({ contentType: 'text/javascript', body: "window.FIREBASE_CONFIG={apiKey:'demo-key',authDomain:'demo-x.firebaseapp.com',projectId:'demo-x',appId:'1:1:web:1'};" }))`.
Seed emulator data over REST with `Authorization: Bearer owner` (bypasses rules).

Check: signed-out features unchanged and persist after reload; sign-in
copies device data; add/edit while signed in shows "saved", survives a
reload; sign-out returns to the device list; phone width (375 px); no
console errors. A 404 for files the deploy generates (e.g. `releases.json`)
is expected locally.

**Keep the check in the repo**, not just in the session: a
`tests/<app>.e2e.mjs` that starts a tiny static server, seeds the emulator
over REST (`Authorization: Bearer owner`), signs in through the fake pop-up
and drives the main features, run with
`firebase emulators:exec --only auth,firestore --project demo-x "node tests/<app>.e2e.mjs"`
as `npm run test:<app>` (Edit 1 Job Board: `tests/board.e2e.mjs`, 13 checks).
Two lessons from writing it:
- **Prove it bites** like the rules tests: break one feature on purpose and
  see a check fail. The first version passed with Undo broken, because the
  Undo bar from the *previous* step was still on screen; checks must assert
  the thing they expect (e.g. the bar names the action just taken).
- In a hand-written Node server, read the file *before* `res.writeHead(200)`;
  `res.writeHead(200).end(await readFile(f))` sends the header first and then
  crashes on a missing file.

**What can't be tested from a cloud session:** a real Google sign-in. The
user does that on the Dev site; tell them so honestly.

### 8b. Privacy page, "Download my data" and "Delete my account" (before real people sign in)

The starter has all three; switch them on for this app:
- **`privacy.html`:** written to cover what the GDPR (EU/UK) and NZ's Privacy
  Act 2020 expect a privacy notice to say: who's responsible and how to reach
  them, what's collected and why (the legal basis), who else handles it
  (Google/Firebase, GitHub hosting, plus e.g. Gmail if the app sends email),
  that Google's sign-in runs in the US (covered by the EU–US Data Privacy
  Framework), how long data is kept, the person's rights and where to
  complain. Ask the user for `{{RESPONSIBLE}}` (a person or trading name) and
  `{{CONTACT}}` (a business/app address they choose to publish, never a
  personal one), and fill in the rest (what's saved, the Firestore region).
  Delete sections that don't apply. It's linked from the sign-in card, the
  menu and Settings. Update it, and its date, whenever the app starts storing
  or sharing something new. Not legal advice: for a business app, suggest
  having it checked.
- **Download my data** (Settings → Your account): a JSON file of everything in
  the account on every stage (the right to a copy), from the same
  `dataCollections` list as Delete.
- **Delete my account** (Settings → Your account, signed in only): set
  `window.AppAccount.dataCollections = ['todos', …]`, every collection under
  `users/{uid}/stages/{stage}/`. It deletes them on **every** stage, then the
  sign-in (`deleteUser`; Google may ask to sign in again first:
  `reauthenticateWithPopup`). The rules must allow the owner to delete
  (`allow delete: if isOwner(userId) && isValidStage(stage)`), with tests.
  Listen for `account:deleted` to clear any copy the app keeps on the device.
- Test it with the emulators: sign in, add data on two stages, delete the
  account, check the data and the emulator user are gone.

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

## A shared team board (not one copy per user)

When several people work on the same data (Edit 1 Job Board):

- **Access list in Firestore, not in the repo:** a document
  `access/members` with `emails: [...]` (lower case), created by Claude
  (`firestore_add_document`) and edited by the owner in the Firebase console.
  Rules: `request.auth.token.email_verified == true && request.auth.token.email.lower() in get(/databases/$(database)/documents/access/members).data.emails`.
  Members may `get` it (the app reads it once to tell "not on the list" apart
  from other errors); nobody may write it from the app. Emails never reach a public repo.
- **Data per stage, shared by members:** `stages/{stage}/boards/{id}`
  (shared), plus `stages/{stage}/tasks/{uid}` for anything personal.
- **No lost updates:** store a `revision` number and save in a
  `runTransaction` that only writes if the revision is unchanged (else show
  "someone else changed this"). Rules enforce
  `revision == (resource == null ? 1 : resource.data.revision + 1)`, plus a
  `mutationId` so a retried save that already landed counts as success.
- **Checking for others' changes without paying for reads:** an
  `onSnapshot` listener on the open document keeps the latest revision in
  memory; don't poll `getDoc` every few seconds (each poll is a billed read).
- **Searching many documents without re-reading them all:** save an
  `updatedAt` server timestamp on every write, read everything once, then
  only query `where('updatedAt', '>=', newestSeen)`. Remember `newestSeen`
  per device and stage (localStorage) only after a full read, because the
  device copy (`getDocsFromCache`) may hold just the documents opened
  earlier, not all of them. (Edit 1 Job Board history search, Nov 2026)
- **Undo on shared data:** keep a snapshot of the data from just before the
  action, show an Undo bar (8 s with a countdown line worked well), and on
  Undo save the snapshot as a normal new revision. Count every time the data
  is replaced from the cloud; if the count changed since the action, refuse
  ("Someone else changed the board just now, so this can't be undone")
  rather than overwrite their work. If a save is still in flight, wait for it
  first. Works alongside an "ask before every action" setting: offer Undo
  after confirming too. (Edit 1 Job Board, issue #12.)
- Storing a big, frequently reshaped object as one JSON **text** field
  (`payload`, size-capped in the rules) keeps rules simple; the trade-off is
  that rules can't validate its inside, so validate in the app.
- Tests: give each test user `{ email, email_verified: true }` via
  `authenticatedContext(uid, { email, email_verified })`, seed the list with
  `withSecurityRulesDisabled`, and test a signed-in non-member and an
  unverified email.

## Adding a field to stored data (e.g. a "done at" time, a "starred" flag)

Strict rules (`keys().hasOnly([...])`) reject any new field, so signed-in
saves would fail if the app ships first. Order (done this way on The Shortlist,
for every new field):

1. Make the field **optional** in the rules (allow absent/null, validate type
   and range) and add it to `onlyChanges([...])` if it changes on update.
2. Add rules tests for it (valid, null, wrong type, out of range, other
   user), run them, and loosen the rule once to prove they fail.
3. Test the app against the emulators **signed in** (save, reload, it comes
   back).
4. **Deploy the rules first**, check them live (`firebase_get_security_rules`),
   then push the app change. Old app versions keep working with the new rules.
   Waiting on something (e.g. a Firebase sign-in)? Push the work to
   `wip/<issue>-<name>`, which doesn't deploy, not to `dev` (The Shortlist #50).
5. Existing records without the field: handle "missing" in the app (e.g. show
   under "Older") rather than inventing values.

## Gotchas

Most setup gotchas are in the steps above (network hosts, support email in
`firebase.json`, authorised domains, `measurementId`, location is permanent,
`firebase_deploy` reporting success without releasing). These are the rest.

**Code and loading**
- **Module vs. classic script order:** `account.js`/data modules are
  `type="module"` (deferred), so a plain `<script>` after them runs **first**
  and finds `window.MyCloud` undefined. Give the plain script `defer`:
  deferred and module scripts run in document order.
- **firebase-admin v14+ has no default `admin` namespace in ES modules**
  (`admin.firestore is not a function`): import from `firebase-admin/app` and
  `firebase-admin/firestore`.

**Rules and tests**
- Proving the rules tests bite: break the rule in a way that still compiles
  (e.g. `return signedIn() || true && ...`); a half-edited function gives a
  compile error, which proves nothing.
- **Write-only collections** (reports, feedback): rules allow `create` for
  people on an allow-list doc (`request.auth.token.email.lower() in
  get(.../access/x).data.emails`, plus `email_verified`), and no read,
  update or delete; the server side reads them with admin access.

**Exporting data**
- **`JSON.stringify` turns Firestore dates into `{seconds, nanoseconds}`
  before a replacer function sees them** (the Timestamp's own `toJSON` runs
  first). Convert dates (`v.toDate().toISOString()`) while copying the data,
  then stringify. Found building "Download my data" (The Shortlist #80).

**Data and money**
- Never delete users' device or cloud data without asking; migrate formats instead.
- Billing stays off (Spark). Anything that needs Blaze (Cloud Functions,
  **every Firebase Extension, e.g. Trigger Email**) needs the user's OK. A
  free-plan way to run server-side work (talk to GitHub, send email) is a
  scheduled **GitHub Action** with the Admin SDK and a service-account key in
  a repo secret: the app writes a doc, the Action picks it up. Say up front
  that it isn't instant: GitHub's shortest schedule is 5 minutes and runs
  often start 5–15 minutes late; scheduled workflows only run from the
  **default branch**. (The Shortlist "Report issue", Nov 2026.)
