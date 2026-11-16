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
