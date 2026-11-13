# Working with the user, and quality checks

## Communication

- The user isn't a developer. Plain English; define technical terms in a
  few words the first time.
- When something is ambiguous, make a sensible choice and say what you
  chose. **Ask first** for anything hard to undo (data deletion, database
  location, production releases, paid services).
- Report honestly: what was tested, what wasn't, what failed.
- End each piece of work with its status: what changed, committed/pushed or
  not, where to see it.
- For visual changes, show a screenshot before pushing.

## Concept first (bigger ideas)

Before building a **new feature or noticeable change** to how the app looks
or works, offer a concept mock-up once (only when there's more than one
reasonable design or the request is vague; not for small tweaks or fixes).

If yes: a clickable mock-up as a **Claude artifact** (not in the repo), 2–3
options side by side with sample data and a short "Good / Watch out" note
each, matching the app's look. Iterate on the same artifact until they pick.
No artifacts available → standalone HTML in the scratchpad + screenshots.
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
- [ ] After pushing: the deploy run succeeded; ask the user to try it on Dev.
