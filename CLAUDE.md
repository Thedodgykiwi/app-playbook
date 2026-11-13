# app-playbook: instructions for Claude

This repo is documentation and templates, not an app. Other projects point
Claude here for how to do common things.

## Keeping it useful

- **Add lessons as you learn them, from any project.** Whenever work on any
  app teaches something useful beyond that app (system, process, tooling,
  hosting, security, design, wording), update the relevant guide in the same
  session (or start a new guide and list it in the README), commit to
  `main`, and tell the user in a line what was added. Fix steps that turned
  out wrong rather than adding contradictions.
- App-specific facts (project IDs, URLs, one app's features) belong in that
  app's own CLAUDE.md, not here.
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
