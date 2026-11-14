# Working with the user, and quality checks

## Communication

- The user isn't a developer. Plain English; define technical terms in a
  few words the first time.
- When something is ambiguous, make a sensible choice and say what you
  chose. **Ask first** for anything hard to undo (data deletion, database
  location, production releases, paid services).
- Report honestly: what was tested, what wasn't, what failed.
- **Every deploy ends with a link.** Whenever something is pushed to Dev or
  promoted to Alpha, Staging or Production, the message ends with the full,
  clickable address of **each** stage that changed (e.g.
  `https://<user>.github.io/<repo>/dev/`), plus one line on what to look at
  there. Never just "it's on Dev". (Added after several updates went out
  without links, Nov 2026.)
- End each piece of work with its status: what changed, committed/pushed or
  not, where to see it.
- For visual changes, show a screenshot before pushing.

## Concept first (bigger ideas)

Offered through the **choice card** every request starts with (`issues.md`):
"Log it + mock-up first" is the recommended option for a **new feature or
noticeable change** to how the app looks or works with more than one
reasonable design or a vague request; not for small tweaks or fixes.

If yes: a clickable mock-up as a **Claude artifact** (not in the repo), 2–3
options side by side with sample data and a short "Good / Watch out" note
each, matching the app's look. Iterate on the same artifact until they pick.
No artifacts available → standalone HTML in the scratchpad + screenshots.
**Build mock-ups from the app itself, not from memory:** inline the app's real
`style.css` and icon set, and copy its real markup (run the app locally,
grab the rendered HTML of the screen with Playwright). Only the new bits get
extra CSS. A hand-styled look-alike drifts (wrong chips, checkboxes,
panels) and the user notices. (Found in test-app, Nov 2026.)

**Before sharing a mock-up, open it in a headless browser** (Playwright),
check for page errors and look at a screenshot. Don't name top-level script
variables after browser globals (`top`, `name`, `parent`, `status`…): the
script stops and every box renders empty. (Found in test-app, Nov 2026.)
Three more from Edit 1 Job Board (Nov 2026): the style kit already uses
short class names such as `.who`, `.avatar`, `.row`, `.state`, so give the
mock-up's own classes distinct names (`.who-row`) or they inherit the
account menu's styling; take dark-mode screenshots after a short wait (the
kit's `.btn` animates its background, so an instant screenshot shows white
buttons); and publish the artifact from the session's scratchpad directory
(files elsewhere, e.g. /tmp, are refused).
**Restyling an existing screen: mock up the real page, not a redraw.**
Run the app locally (emulators + seeded sample data covering every state),
save the rendered page with Playwright (`documentElement.cloneNode`, drop
scripts, dialogs and Firebase's hidden `<iframe>`), inline its CSS, and put
the new look in **one extra stylesheet** with a "New look / Current look"
toggle. Every control and state then comes from the real app, and that
stylesheet is most of the build. A hand-drawn redraw of Edit 1 Job Board
silently dropped buttons, a drop-down and the job-state colours, and changed
the button order; the user caught it (Nov 2026).
**Before proposing to merge two steps into one** (e.g. "pick + send" →
"pick = send"), check whether the in-between state means something on its own
and ask if unsure. In Edit 1 Job Board, picking an editor without sending
*pre-assigns* a job (held in the queue in case plans change); all three
one-tap mock-up options broke that and were rejected. The fix that worked was
making each state clearer instead (hide the button until an editor is picked,
label it "Send to Tom"). Nov 2026.
Never put concept code in the repo.

## Guardrails

- No secrets or personal data in repos (including support emails in config files).
- Ask before adding external libraries, third-party services, tracking or
  analytics, or anything that costs money or needs an account.
  Dev-only test packages in `package.json` are fine once agreed; the app
  itself must not depend on `node_modules` if it has no build step.
- Don't delete or reset user data (browser storage, cloud data) without
  asking; if the format changes, migrate it.

## Before pushing

- [ ] No errors in the browser console.
- [ ] Existing features still work (list them in the app's CLAUDE.md),
      including that saved data persists after a reload.
- [ ] Phone width (~375 px) and desktop both look right, no sideways scroll.
- [ ] Accessibility: labelled buttons and inputs, good contrast, works
      with the keyboard (Tab, Enter, Escape closes menus).
- [ ] Small, focused commits: one feature or fix each, message says what and why.
- [ ] After pushing: the deploy run succeeded; **try the change on the live
      Dev site straight after the page loads** (not only after waiting):
      start-up work such as a sign-in check can redraw the page and expose
      bugs a slow local test misses. Then ask the user to try it on Dev.
