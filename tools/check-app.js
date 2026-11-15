// Basic safety-net check for any playbook app. Shared by every app (one copy,
// in the playbook; never copy it into an app).
//
// Opens each page at phone (375px) and desktop (1280px) width, in light and
// dark, and fails if any of these happen:
//   - a JavaScript error or console error
//   - a file the page needs fails to load (404 etc.)
//   - the "Oops, something went wrong" start-up screen appears
//   - the page scrolls sideways (something wider than the screen)
//
//   node <playbook>/tools/check-app.js                  # app in current folder
//   node <playbook>/tools/check-app.js --dir ../my-app --pages "/,/styleguide.html,/#/jobs"
//   node <playbook>/tools/check-app.js --url https://<user>.github.io/<repo>/dev/
//
// --pages: comma-separated paths (default "/,/styleguide.html"). An app lists
// its main screens in its CLAUDE.md ("Checks") so every session runs the same.
// --ignore: comma-separated file names whose 404s are fine (default:
// releases.json, which only the deploy creates; checked anyway with --url).
// --shots <dir>: also save a screenshot of every page/size/theme there.
// Needs Node + Playwright (pre-installed in Claude cloud sessions).
const http = require('http');
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const args = Object.fromEntries(process.argv.slice(2).reduce((a, v, i, all) =>
  (v.startsWith('--') ? a.concat([[v.slice(2), all[i + 1]]]) : a), []));
const dir = path.resolve(args.dir || '.');
const pages = (args.pages || '/,/styleguide.html').split(',').map(s => s.trim()).filter(Boolean);
const ignore = (args.ignore ?? (args.url ? '' : 'releases.json')).split(',').map(s => s.trim()).filter(Boolean);
const SIZES = [['phone', 375, 812], ['desktop', 1280, 800]];
const THEMES = ['light', 'dark'];
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.css': 'text/css',
  '.json': 'application/json', '.webmanifest': 'application/manifest+json', '.svg': 'image/svg+xml',
  '.png': 'image/png', '.jpg': 'image/jpeg', '.ico': 'image/x-icon', '.woff2': 'font/woff2' };

function serve() {
  return new Promise(resolve => {
    const server = http.createServer((req, res) => {
      let p = decodeURIComponent(req.url.split('?')[0]);
      let file = path.join(dir, p);
      if (!file.startsWith(dir)) { res.writeHead(403); return res.end(); }
      if (fs.existsSync(file) && fs.statSync(file).isDirectory()) file = path.join(file, 'index.html');
      fs.readFile(file, (err, data) => {
        if (err) { res.writeHead(404); return res.end('Not found'); }
        res.writeHead(200, { 'Content-Type': TYPES[path.extname(file)] || 'application/octet-stream' });
        res.end(data);
      });
    }).listen(0, '127.0.0.1', () => resolve(server));
  });
}

(async () => {
  let server, base = args.url;
  if (!base) {
    if (!fs.existsSync(path.join(dir, 'index.html'))) { console.error(`No index.html in ${dir}`); process.exit(2); }
    server = await serve();
    base = `http://127.0.0.1:${server.address().port}/`;
  }
  if (!base.endsWith('/')) base += '/';
  if (args.shots) fs.mkdirSync(args.shots, { recursive: true });

  const browser = await chromium.launch();
  const failures = [];
  let runs = 0;
  for (const pagePath of pages) {
    for (const [sizeName, width, height] of SIZES) {
      for (const theme of THEMES) {
        runs++;
        const label = `${pagePath} (${sizeName}, ${theme})`;
        const ctx = await browser.newContext({ viewport: { width, height }, colorScheme: theme, serviceWorkers: 'block' });
        const page = await ctx.newPage();
        const problems = [];
        page.on('pageerror', e => problems.push(`script error: ${e.message}`));
        page.on('console', m => { if (m.type() === 'error' && !m.text().startsWith('Failed to load resource')) problems.push(`console error: ${m.text()}`); });
        page.on('response', r => { if (r.status() >= 400 && !ignore.some(f => new URL(r.url()).pathname.endsWith('/' + f))) problems.push(`failed to load (${r.status()}): ${r.url()}`); });
        try {
          await page.goto(new URL(pagePath.replace(/^\//, ''), base).href, { waitUntil: 'networkidle', timeout: 20000 });
          await page.waitForTimeout(500);
          if (await page.locator('.error-screen').count()) problems.push('the "something went wrong" start-up screen is showing');
          const over = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
          if (over > 1) problems.push(`scrolls sideways by ${over}px`);
          if (args.shots) await page.screenshot({ path: path.join(args.shots,
            `${pagePath.replace(/[^a-z0-9]+/gi, '_') || 'home'}-${sizeName}-${theme}.png`), fullPage: true });
        } catch (e) {
          problems.push(`page didn't load: ${e.message.split('\n')[0]}`);
        }
        await ctx.close();
        // Same problem at every size/theme? Report it once per page.
        for (const p of [...new Set(problems)]) failures.push(`${label}: ${p}`);
      }
    }
  }
  await browser.close();
  if (server) server.close();

  if (failures.length) {
    console.log(`FAILED: ${failures.length} problem(s) in ${runs} checks\n`);
    for (const f of failures) console.log(' - ' + f);
    process.exit(1);
  }
  console.log(`PASSED: ${pages.length} page(s) x phone/desktop x light/dark (${runs} checks), no errors, no sideways scrolling.`);
})();
