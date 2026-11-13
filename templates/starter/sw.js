// Service worker: lets the app open without a connection.
// Registered by pwa.js. Each stage has its own (its scope is the stage's
// folder), and Production's ignores the test stages' folders inside it.
//
// How it fetches:
// - The page itself: network first (always the newest when online), the
//   saved copy when offline.
// - Files with ?v=<build> (the deploy adds this to CSS/JS/icons): saved copy
//   first; a new build has new addresses, so they're never stale.
// - Other files from this app (e.g. releases.json, local copies without
//   ?v=): network first, saved copy when offline.
// - The Firebase library from gstatic (its address includes its version):
//   saved copy first, so sign-in code loads offline too.
// - Everything else (Google sign-in, the database): left to the browser.
const CACHE = 'app-' + new URL(self.registration.scope).pathname;
const SCOPE = self.registration.scope;
const OTHER_STAGES = /\/(dev|alpha|staging|pipeline)\//;

self.addEventListener('install', (event) => {
  // Save the page and every versioned file it links to, ready for offline use.
  event.waitUntil((async () => {
    const cache = await caches.open(CACHE);
    const res = await fetch(SCOPE, { cache: 'no-store' });
    if (!res.ok) return;
    const html = await res.clone().text();
    await cache.put(SCOPE, res);
    const files = [...html.matchAll(/(?:href|src)="([^":]+\?v=[^"]+)"/g)].map((m) => new URL(m[1], SCOPE).href);
    await Promise.all(files.map((u) => cache.add(u).catch(() => {})));
  })());
  self.skipWaiting();
});

self.addEventListener('activate', (event) => event.waitUntil(self.clients.claim()));

self.addEventListener('fetch', (event) => {
  const req = event.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  const own = url.href.startsWith(SCOPE);
  // Production's scope contains the test stages: leave their requests alone.
  if (own && OTHER_STAGES.test(url.pathname.slice(new URL(SCOPE).pathname.length - 1))) return;

  if (req.mode === 'navigate' && own) return event.respondWith(networkFirst(req, SCOPE));
  if (own && url.searchParams.has('v')) return event.respondWith(cacheFirst(req, true));
  if (own) return event.respondWith(networkFirst(req));
  if (url.hostname === 'www.gstatic.com' && url.pathname.startsWith('/firebasejs/')) return event.respondWith(cacheFirst(req));
});

async function networkFirst(req, key = req) {
  const cache = await caches.open(CACHE);
  try {
    const res = await fetch(req);
    if (res.ok) cache.put(key, res.clone());
    return res;
  } catch (err) {
    const saved = await cache.match(key, { ignoreSearch: req.mode === 'navigate' });
    if (saved) return saved;
    throw err;
  }
}

async function cacheFirst(req, dropOldBuilds = false) {
  const cache = await caches.open(CACHE);
  const saved = await cache.match(req);
  if (saved) return saved;
  const res = await fetch(req);
  if (res.ok) {
    if (dropOldBuilds) {  // forget older builds of the same file
      const path = new URL(req.url).pathname;
      for (const k of await cache.keys()) {
        if (new URL(k.url).pathname === path && k.url !== req.url) cache.delete(k);
      }
    }
    cache.put(req, res.clone());
  }
  return res;
}
