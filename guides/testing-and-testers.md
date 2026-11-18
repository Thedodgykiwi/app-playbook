# Testing: the automatic check and people testing each stage

Two layers: a quick **automatic check** that every session runs before
pushing, and **people** trying the app at Alpha and Staging before anything
reaches Production.

Last verified: 2026-11-18 (check run on the starter and on test-app's Dev).

## 1. The automatic check (every app, every push)

One shared tool in the playbook, `tools/check-app.js` (never copied into
apps). It opens each page at phone (375px) and desktop width, in light and
dark, and fails on:

- a script error or console error;
- a file that fails to load;
- the "Oops, something went wrong" start-up screen;
- anything that makes the page scroll sideways.

```bash
# from the app repo, with the playbook cloned next to it (/home/user/app-playbook)
node /home/user/app-playbook/tools/check-app.js --pages "/,/styleguide.html"
# after the deploy, against the live stage:
node /home/user/app-playbook/tools/check-app.js --url https://<user>.github.io/<repo>/dev/
# with screenshots to look at:
node /home/user/app-playbook/tools/check-app.js --shots <scratchpad>/shots
```

- The app's `CLAUDE.md` ("Checks") lists the pages/screens to pass to
  `--pages` (e.g. `/#/jobs`) plus any app-specific tests
  (`npm run test:rules`…). Add a screen there when you build it.
- Locally, `releases.json` 404s are ignored (only the deploy makes it).
- It's a **safety net, not proof**: it doesn't click through features. Still
  look at the change (screenshots, measuring alignment: `design.md`), and
  for logic that's easy to get wrong (dates, totals, sync, permissions) add a
  small test the app keeps and list it under "Checks".
- A failure is fixed before pushing, never skipped. If it's a false alarm
  (e.g. a known third-party warning), fix the tool here in the playbook so
  every app benefits, rather than ignoring it in one app.

## 2. People testing each stage

What each stage is for, so everyone knows what "ready" means:

| Stage | Who tries it | What they check | Ready to move on when |
|---|---|---|---|
| **Dev** | Claude + the user | The change works and looks right | User is happy with it on Dev |
| **Alpha** | The user (and friendly testers) | Real use on their own phone; the brief's success checks still pass | No new bugs from this batch, or they're logged and agreed to wait |
| **Staging** | Testers / the client | The release as it will ship; quick run through the main moment (brief) | Tester sign-off (below) |
| **Production** | Everyone | — | — |

Small apps used only by you can skip testers: Alpha and Staging are then
just your own check on your phone. Say so in the app's `CLAUDE.md`.

### When promoting

- **To Alpha or Staging:** the promote message to the user includes a short
  **"what to try"** list (2–5 plain steps, from the issues in this batch and
  the brief's success checks), plus the stage link. The user can forward it to
  testers as-is.
- **To Production:** before asking for the "yes", give a one-line **sign-off
  summary**: what was tested on Staging, by whom (role), anything known and
  accepted. No sign-off yet → say so; Production still only needs the user's
  "yes", but they decide knowing that.

### Feedback from testers

- Each problem or idea becomes an issue in the usual layout (`issues.md`),
  "Reported by: tester" (or "client"), with the **stage** under "Where".
  Screenshots go in `.github/issue-screenshots/` (`issues.md`).
- A bug in something just promoted → a sub-issue of that change's issue
  (`issues.md`). It blocks the next promotion unless the user says it can wait.
- Testers don't need GitHub: they tell the user (message, screenshot), or use
  the app's "Report a problem" link where it has one; Claude logs it.
