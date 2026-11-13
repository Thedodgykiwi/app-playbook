# Working in Claude Code cloud sessions

Notes for Claude when running in a claude.ai/code cloud container.

## Network

- The network is **limited by default**. A blocked host shows up as
  `CONNECT tunnel failed, response 403` / `ERR_TUNNEL_CONNECTION_FAILED`.
  `curl -sS "$HTTPS_PROXY/__agentproxy/status"` lists recent refusals.
- Don't add app-specific hosts to the user's **Default** environment.
  Create a **personal environment named after the repo** (`create_environment`
  with `switch_session: network_only`, `repositories: ["owner/repo"]`), and add
  hosts to it later with `update_environment`. The user approves each change.
- Ask for the whole list at once where you can (see the Firebase guide for
  its list). Always include `<username>.github.io` so you can check the live site.
- Changes apply within seconds; retry once after ~30 s if still blocked.
- Tools that don't use the proxy keep the old rules until the machine is
  replaced.

## Repos

- Claude can't create GitHub repos. The user creates them, then
  `add_repo` + clone + `register_repo_root`.
- No `gh` CLI (except `gh api ... search/...`); use the GitHub MCP tools,
  e.g. `actions_list` to check deploy runs.
- Commit only to the branches the session/CLAUDE.md allow.

## Files

- The **scratchpad** (and the whole container) is deleted when the session
  ends. Anything worth keeping (tests, tools, notes) must go in a repo.
- Files the user should open must be inside the repo directory or the scratchpad.

## Logins

- Firebase: `firebase_login` from the Firebase plugin; show URL **and**
  session ID; the login lasts for this session only.
- Keys/tokens for other APIs: use `request_credential`, never ask the user
  to paste secrets into chat, never commit them.

## Waiting for things

- Plain `sleep N` is blocked. Use a loop on a condition
  (`until <check>; do sleep 10; done`) or `run_in_background`.
- Firebase deploys are asynchronous: poll `firebase_deploy_status`.
- Stop background servers/emulators (TaskStop) when done.

## Browser testing

- Chromium + Playwright are pre-installed: `require('playwright')`, no install.
- Screenshots for the user at `deviceScaleFactor: 2`; for your own checks, 1.
- Real third-party sign-ins (Google etc.) can't be completed here; test
  with emulators and have the user try the real thing on Dev.

## Instructions that apply to every session

Cloud sessions don't read `~/.claude/CLAUDE.md` from the user's computer,
and the personal-preferences box in Claude's chat settings isn't documented
to reach them. To give Claude standing instructions in **every** cloud
session (e.g. "use the app-playbook"), add a **setup script** to the cloud
environment that writes the file:

```bash
#!/bin/bash
mkdir -p ~/.claude
cat > ~/.claude/CLAUDE.md <<'EOT'
<instructions>
EOT
```

- Put it on **each** environment the user uses (the Default one too:
  that's where brand-new apps start). Claude can only change the environment
  the current session runs on (`update_environment`); the user adds it to
  others under the environment's settings (Edit → Setup script).
- It runs when a fresh container starts, not on a resume. Check with
  `/context` that `/root/.claude/CLAUDE.md` appears under Memory files.
- It's visible to anyone who can use the environment: no secrets.
