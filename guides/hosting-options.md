# Hosting options beyond GitHub Pages (reference only)

**Status: not in use, not tested.** Every app still deploys to GitHub Pages
(`github-pages.md`). This page records the options looked at (Nov 2026) and
the simplest one to try first, so a future session doesn't start from
scratch. Prices and plan rules change: re-check them before acting.

## Why look beyond GitHub Pages

- **Private repos:** a private repo's Pages site needs a paid GitHub plan
  (Pro, about US$4/month). Private repos also make issues (tester reports)
  private.
- **No 10-minute stale cache** after a deploy.
- **Instant rollback** from the host's dashboard.

## Options compared

| Host | Private repos | Good for | Watch out |
|---|---|---|---|
| **Netlify** | Free | Static apps like ours | One more account and token |
| **Cloudflare Pages** | Free | Same; fastest network | Same |
| **Vercel** | Free | Same | Free (Hobby) plan is **non-commercial only**: client apps need Pro (~US$20/month) |
| **Hostinger, basic hosting** | Yes (deploy key) | Own domain, already paid for | Its Git deploy only copies files: no build step |
| **Hostinger, web apps / Node.js ("Claude Code hosting")** | Yes | Apps that need a running server | Pays for server features static apps don't use; each stage likely a separate app |

## The simplest test (recommended first step)

**Keep the build in GitHub; only change where the files go.** The shared
deploy (`deploy-stages.yml`) already does the stage work (stage name, icons,
release notes, cache-busting). Swap its last step from "publish to GitHub
Pages" to an upload of the finished folder:

- Netlify: `netlify deploy --dir <built folder> --prod` (site per stage, or
  branch deploys), token in GitHub secrets.
- Vercel: `vercel deploy --prebuilt`; Hostinger basic: upload over SFTP.

Automatic: the upload is one extra step in the deploy job, using an access
token from the host saved in the repo's GitHub secrets; every push to a
stage branch deploys, as now. (The alternative, linking the repo in the
host's dashboard so it builds, means redoing the stage steps their way.)

Why upload rather than let the host build: fast (no package install or
compile; the job takes about a minute, the upload seconds, changed files
only), the same steps for any host, and the exact files that were built go
live. Downsides (small): failure details are in GitHub's log, not the
host's; the host's "Redeploy" can only restore an earlier upload; the token
can expire; the host's per-pull-request previews go unused (stages do that
job); it uses GitHub Actions minutes.

Try it on **one app's Dev stage only**, then add it to the shared deploy as
an option. Ask the user first: it needs their account on that host.

## Things that change when moving (checklist)

- [ ] Each stage gets its own address (e.g. `dev--app.netlify.app`) instead
      of `/dev/` folders. Fine: browser storage is then separate anyway.
- [ ] Add every new address to Firebase → Authentication → Authorised
      domains, or sign-in fails.
- [ ] Update addresses that point at the old site: the app's CLAUDE.md stage
      table, the "Report issue" job's release-notes URL (`<APP_URL>`), links
      in deploy messages.
- [ ] Signed-out device data stays at the old address (users signed in are
      fine); home-screen shortcuts need re-adding.
- [ ] Private repo on a free GitHub plan: Actions minutes are limited; the
      5-minute "Report issue" job uses them.

## Custom domains (any host, including GitHub Pages)

Point a DNS record at the host (a subdomain such as `app.example.com` with a
CNAME is simplest), set the domain in the host's settings, turn on HTTPS,
add the domain to Firebase's authorised domains. Never use a registrar's
"forwarding / masking" option: it frames the app and breaks sign-in,
offline and install.
