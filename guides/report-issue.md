# "Report issue": testers report straight from the app

Last verified: 2026-11-15 (test-app, issues #28 and #34).

An optional extra for any app with Google sign-in. Testers tap **Report issue**
on the stage banner (Dev, Alpha, Staging; never Production), fill in a title,
a description and an optional type, and:

1. the report is saved to the app's Firestore (testers only);
2. every few minutes a GitHub Action turns it into a **GitHub issue** in the
   standard layout (`issues.md`, "Reported by: tester", the type as its
   label) and emails the tester a **receipt**;
3. when a change for that issue reaches **Production**, the tester gets a
   second email, **"it's now live"**, with the release-note line for it.

Free plan throughout (no Firebase billing, no new accounts besides a Gmail
app password). Issues and emails arrive **5–15 minutes** after a report
(GitHub's schedule), so say that when offering it.

## Your part: 4 things per app (the only steps that differ each time)

Everything else (button, rules, workflow) Claude sets up from the templates.
These four need the app owner, once per app. Claude gives the exact links.

| # | What | Where | Notes |
|---|---|---|---|
| 1 | **`FIREBASE_SERVICE_ACCOUNT`** secret | Firebase console → that app's project → Project settings → Service accounts → **Generate new private key**: `https://console.firebase.google.com/project/<project-id>/settings/serviceaccounts/adminsdk`. Paste the whole file as a new secret at `https://github.com/<owner>/<repo>/settings/secrets/actions`, then delete the file. | **Different for every app** (each app has its own Firebase project). |
| 2 | **`GMAIL_USER`** secret | Same GitHub secrets page. | The sending Gmail address. Same value for every app. |
| 3 | **`GMAIL_APP_PASSWORD`** secret | Make one at `https://myaccount.google.com/apppasswords` (signed in as that Gmail), add on the same page. | Same value for every app (or one per app). "Not available for your account" = turn on 2-Step Verification first. Never paste it into a chat. |
| 4 | **Testers list** | Firestore → `access` → `testers`, field `emails` (array of lower-case addresses): `https://console.firebase.google.com/project/<project-id>/firestore/databases/-default-/data/~2Faccess~2Ftesters`. Claude can create it with your go-ahead. | **Separate from the app's own allow list** (e.g. `access/members`): someone can be a tester without using the app, or use the app without being a tester. Never in the repo. |

Secrets belong to the **repo**, not to a stage: set once, they work for Dev,
Alpha and Staging. Do 1–3 **before the first test report**: a report
collected while the Gmail secrets are missing never gets its emails.
Check: Actions → "Turn reports into issues" → Run workflow; the log must
not say "secret not set".

## What's shared and what each app owns

| Piece | Where |
|---|---|
| The job (issues + both emails) | **Shared, one copy:** `.github/scripts/issue_reports.mjs`, run by the shared workflow `.github/workflows/issue-reports.yml`. Never copy it into an app. |
| Small workflow that calls it on a schedule | App: `.github/workflows/issue-reports.yml` (template in `templates/.github/workflows/`) |
| Button + drop-down | App: `report.js`, its CSS and the banner button (in the starter; off until `window.REPORT_ISSUES = true` in `firebase-config.js`) |
| Who may report; the reports collection | App: `firestore.rules` `issueReports` block + its tests (in `templates/firebase/`) |
| Testers list | App's Firestore: `access/testers` `{ emails: [...] }`, edited in the console, **never in the repo** |

## Ask the user first

Offer it with the choice card like any feature. Before building, confirm:
- the app has (or will get) Google sign-in (`firebase-auth-and-firestore.md`);
- which Gmail sends the emails (it needs 2-Step Verification on, for an app
  password; Google Workspace accounts may not offer app passwords);
- who the first testers are (their addresses go only into Firestore).

## Switching it on (checklist)

1. **Code** (apps from the starter already have it):
   - `report.js`, the `#report-link` button in the banner, the "Report
     issue" CSS block, the `flag` icon; `report.js` loads after `app.js`.
   - Older apps without `account.js`: give `report.js` the same small
     `cloud` object (current user, sign in, save the report) from the app's
     own sign-in code (test-app does this from `sync.js`).
   - `window.REPORT_ISSUES = true;` in `firebase-config.js`.
   - Apps with a sign-in / access **gate** that covers the page: give
     `.report-box` a higher z-index than the gate, so a tester who is
     locked out can still report (Edit 1 Job Board: gate 50, box 60).
   - Apps not on the starter's style kit: map its CSS variables
     (`--surface`, `--accent`, `--danger`) and button classes to the app's
     own, and inline the three icons if the app has no `icon()`.
2. **Rules:** copy the `issueReports` block (and the comment) from
   `templates/firebase/firestore.rules`, and its tests; run `npm run
   test:rules`; deploy, then **check the live rules** (the MCP deploy can
   report success without releasing: `firebase-auth-and-firestore.md`).
3. **Testers list:** create `access/testers` with field `emails` (array of
   lower-case addresses) in the Firebase console, or with the Firebase MCP
   `firestore_update_document`.
4. **Workflow:** copy `templates/.github/workflows/issue-reports.yml`, set
   `app_name` and `app_url` (Production address). Push to `dev` (scheduled
   runs only use the default branch's copy).
5. **Secrets and testers list:** the owner's part, "Your part" table above.
   Give them the exact links for this app; never ask for the values in chat.
6. **Test:** a tester sends a report on Dev; run the workflow (Actions → Turn
   reports into issues → Run workflow, or `actions_run_trigger`); check the
   issue, the report's `status: logged` in Firestore, and the email.

## How it behaves (for answering questions)

- Report statuses: `new` → `logged` (issue created, receipt sent) → `fixed`
  ("now live" email sent) or `closed` (issue closed without a Production
  release, or "not planned": no email).
- The "now live" email only goes out when the issue is closed **and** its
  number appears in Production's release notes (a bullet ending "(#n)" in
  `<app_url>/releases.json`). Closing a test issue by hand never emails
  anyone. A fresh close gets an hour's grace for the release notes to publish.
- The tester's address is stored only in Firestore (not readable from the
  app), kept until the second email (or the close), then deleted. Issues
  never contain names or addresses; "@mentions" in reports are neutralised.
- Without `FIREBASE_SERVICE_ACCOUNT` the job does nothing; without the Gmail
  secrets it creates issues but sends no email (and those reports never get
  emails later).
- Wording: never promise a fix (`design.md`, "Wording"). The app's thank-you
  says only "We'll email you a copy shortly"; no GitHub details for testers.

## Testing the job locally

Run the shared script against the Firestore emulator with a fake GitHub:
`FIRESTORE_EMULATOR_HOST=127.0.0.1:<port> GITHUB_API_URL=http://127.0.0.1:<fake>
APP_URL=http://127.0.0.1:<fake>/ GITHUB_TOKEN=x GITHUB_REPOSITORY=o/r MAIL_TEST=1
node .github/scripts/issue_reports.mjs` (after `npm install --no-save
firebase-admin@14 nodemailer@10` beside it). `MAIL_TEST=1` builds the emails
and sends nothing. The fake server answers `POST /repos/o/r/issues`,
`GET /repos/o/r/issues/<n>` and `GET /releases.json`.
