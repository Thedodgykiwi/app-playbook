# New app kickoff: plan and desired outcome

Run this **once per new app**, straight after the setup in the `new-app` skill
(or `new-app-setup.md`) and **before any feature code**. It produces the app's
**brief** (`docs/brief.md` in the app repo): the goal, who it's for, what v1
must do, and how we'll know it works. Every later session reads the brief
(session checklist, step 1), so nobody has to relearn the plan in a new thread.

Why: setup answers *how* to build and ship; nothing answered *what* to build
or what "done" looks like. Without a written goal, each session sees only one
issue at a time and guesses at scope.

**Flexible by design.** The brief is a living document, not a contract. Ideas
change; when they do, update the brief (section 5) rather than working around
it. A short brief that is current beats a long one that is stale.

## 1. Understand the idea (ask, don't assume)

Ask in **one message**, plain English, a few questions at a time. Accept
"don't know yet" and record it under *Open questions*; don't block on it.

- [ ] **Problem:** what's annoying, slow or missing today? How is it done now
      (paper, spreadsheet, another app, not at all)?
- [ ] **People:** who uses it, by role ("me", "our drivers", "the client's
      office staff"), never by name. One person or several? Do they share data?
- [ ] **Where and when:** phone, desktop or both? On the go, in a hurry,
      offline (a site with no signal)?
- [ ] **The main moment:** describe one typical use from opening the app to
      closing it. This becomes the main screen.
- [ ] **Desired outcome:** what is different when it works? Ask for something
      you could check: "quotes go out the same day", "nothing gets lost
      between shifts", "I stop using the spreadsheet".
- [ ] **Must-haves for v1:** the 3–7 things it must do to be useful at all.
- [ ] **Not now:** nice ideas that wait for later (write them down so they
      aren't lost, and so v1 stays small).
- [ ] **Constraints:** sign-in / cloud data needed? Anything private or
      sensitive? Budget (anything that costs money needs a "yes")? Deadline?
      Existing data to bring in?

Already have a long description from the user? Fill the brief from it and
ask only about the gaps.

## 2. Write the brief

- [ ] Fill in `docs/brief.md` (the starter includes the template; copy of it:
      `templates/starter/docs/brief.md`). Keep it to about one page.
- [ ] Turn the outcome into **2–4 success checks**: things the user can see or
      try ("a new job can be added on a phone in under 30 seconds").
- [ ] Note **assumptions** you made, so they can be challenged.
- [ ] No personal data, client names or secrets: the repo is public.

## 3. Shape v1

- [ ] **Screens:** list the few screens v1 needs and what's on each, in words.
- [ ] **Data:** what the app keeps (e.g. "a job: customer, address, date,
      status"), and where (this device only, or cloud via sign-in).
- [ ] **Mock-up the main screen first** (concept mock-up, 2–3 options, in an
      artifact: `working-with-the-user.md`). Design decisions are cheapest now.
- [ ] Pick the app's accent colour and icon if not done in setup (`design.md`).

## 4. Agree the plan, then log it

- [ ] Show the user the brief and the v1 plan in plain English. **Get their
      OK before any feature code.** Adjust and re-show if they change things.
- [ ] Create one **`feature` issue per must-have** (usual layout,
      `issues.md`), and one parent issue **"v1: <app name>"** with them as
      **sub-issues**, in build order. Put the order in the brief's *Plan*.
- [ ] "Not now" ideas: keep them in the brief, or log them as issues with
      `priority: low` if the user prefers.
- [ ] Commit `docs/brief.md` on `dev` (`docs/` counts as housekeeping, so it
      doesn't trigger a release on its own).

Build order rule of thumb: the **main moment** end-to-end first (even rough),
then the other must-haves, then polish. Something usable on Dev early beats
every screen half-done.

## 5. Keeping the brief current (every session)

The session checklist points every session at the brief. During any session:

- [ ] A request **fits the brief** → carry on as normal.
- [ ] A request **changes the goal, the people, a must-have or "not now"** →
      say so in one line ("this changes the plan: X"), and with the user's OK
      update the brief in the same commit as the issue/work. Add a line to its
      *Change log* (date + what changed + why).
- [ ] A request **conflicts** with the brief (e.g. something listed as "not
      now", or against a constraint) → point it out and ask; the user decides,
      the brief records it.
- [ ] A must-have is **done** (released to Production) → tick it in the brief.
- [ ] All v1 must-haves done → check the success checks with the user, then
      agree the next set ("v2" parent issue) the same way (sections 3–4).

## 6. Existing apps without a brief

When a session finds an app with no `docs/brief.md`, offer (don't force) to
write one: draft it from the app's `CLAUDE.md`, open issues and what the app
already does, then ask the user to fill the gaps (mainly the desired outcome).
