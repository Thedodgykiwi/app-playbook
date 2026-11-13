# app-playbook: instructions for Claude

This repo is documentation and templates, not an app. Other projects point
Claude here for how to do common things.

## Keeping it useful

- **Add lessons as you learn them.** When a project hits a new gotcha or a
  step was missing or wrong, update the relevant guide (or the gotchas list
  at the end of it) in the same session, and tell the user.
- Prefer **checklists and exact commands** over prose. Say *why* for
  anything surprising.
- Put a "Last verified" date on guides with version-specific steps and
  update it when you re-verify.
- Keep templates **generic** ("My App", `YOUR-PROJECT-ID`), and keep them
  in step with the worked example (`Thedodgykiwi/test-app`) when it improves.
- Write so someone who isn't a developer can follow the gist.

## Never put in this repo

- Secrets: passwords, API keys, tokens, private keys.
- Personal data: email addresses, names of end users, real user data.
- Real Firebase config values (use placeholders).

## Commits

Small and focused, with a message saying what changed and why.
