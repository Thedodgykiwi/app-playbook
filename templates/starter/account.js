// Google sign-in (Firebase Authentication) + access to Cloud Firestore.
//
// Dormant until firebase-config.js has the app's settings: while it's null
// this file does nothing and no sign-in button shows (the app menu in menu.js
// still works). Signed in, the menu shows your Google photo, name and email. To switch it on, follow
// the playbook's firebase-auth-and-firestore.md (project, rules + tests,
// authorised domain, emulator testing).
//
// What it gives the rest of the app (no to-do or other app data here: each
// app saves its own data; see test-app's sync.js for a worked example):
//   window.addEventListener('account:change', (e) => e.detail.user)  // signed in (user) or out (null)
//   await window.AppAccount.ready   // { auth, authLib, db, fs } once Firebase has loaded (null if off)
//   window.AppAccount.user          // current user or null
//   window.AppAccount.setStatus({ saving, error })   // shows/updates the menu's sync status (hidden until first called)
// Store each user's data per stage, e.g. users/{uid}/stages/{stage}/...,
// because all stages share one web address and one sign-in.
//
// The Firebase library loads from Google's CDN as ES modules (no build step).
// Pinned version: update it deliberately, not automatically.
const SDK = 'https://www.gstatic.com/firebasejs/13.1.0';

const config = window.FIREBASE_CONFIG;
// Every app on <user>.github.io shares browser storage: keep keys per app.
const SIGNED_IN_KEY = `signed-in:${location.pathname.split('/')[1] || 'app'}`;
let resolveReady;
window.AppAccount = { user: null, ready: new Promise((r) => { resolveReady = r; }), setStatus() {} };
if (!config) resolveReady(null);
else start().catch((err) => {
  // Couldn't load Firebase (e.g. offline on first visit): the app keeps working signed out.
  console.warn('Sign-in unavailable:', err);
  resolveReady(null);
});

async function start() {
  const [{ initializeApp }, authLib, fs] = await Promise.all([
    import(`${SDK}/firebase-app.js`),
    import(`${SDK}/firebase-auth.js`),
    import(`${SDK}/firebase-firestore.js`),
  ]);
  const fbApp = initializeApp(config);
  const auth = authLib.getAuth(fbApp);
  const db = fs.initializeFirestore(fbApp, {
    localCache: fs.persistentLocalCache({ tabManager: fs.persistentMultipleTabManager() }),
  });

  // Local testing against the Firebase emulators: http://localhost:8080/?emulators
  if (['localhost', '127.0.0.1'].includes(location.hostname) && new URLSearchParams(location.search).has('emulators')) {
    authLib.connectAuthEmulator(auth, 'http://127.0.0.1:9099', { disableWarnings: true });
    fs.connectFirestoreEmulator(db, '127.0.0.1', 8081);
  }
  resolveReady({ auth, authLib, db, fs });

  const $ = (id) => document.getElementById(id);
  const ui = {
    box: $('account'), signIn: $('sign-in'), button: $('account-btn'), avatar: $('avatar'),
    avatarImg: $('avatar-img'), who: $('who'), whoImg: $('who-img'), whoLetter: $('who-letter'),
    dot: $('sync-dot'), name: $('account-name'), email: $('account-email'),
    status: $('sync-status'), signOut: $('sign-out'),
  };
  // The menu itself (open/close, theme, Settings, version) is menu.js.
  const setMenu = () => window.AppMenu?.close();
  const signedOutAvatar = ui.avatar.innerHTML;   // the generic person icon

  // Google photo, falling back to the first letter if there's none or it fails to load.
  function showPhoto(img, letterEl, url, letter) {
    letterEl.textContent = letter;
    img.hidden = !url; letterEl.hidden = !!url;
    if (url) {
      img.onerror = () => { img.hidden = true; letterEl.hidden = false; };
      img.src = url;
    }
  }

  ui.signIn.addEventListener('click', async () => {
    try {
      await authLib.signInWithPopup(auth, new authLib.GoogleAuthProvider());
    } catch (err) {
      const msg = {
        'auth/popup-closed-by-user': null,
        'auth/cancelled-popup-request': null,
        'auth/popup-blocked': 'Your browser blocked the sign-in window. Allow pop-ups for this site and try again.',
        'auth/network-request-failed': "Couldn't reach Google. Check your connection and try again.",
        'auth/unauthorized-domain': "Sign-in isn't set up for this web address yet.",
      }[err.code];
      if (msg !== null) toast(msg || `Sign-in didn't work (${err.code || err.message}).`, 6000);
    }
  });
  ui.signOut.addEventListener('click', () => { setMenu(false); authLib.signOut(auth); });

  // ---- Sync status (the app reports saving/errors via AppAccount.setStatus) ----
  // Hidden until the app first reports saving (setStatus), so an app that
  // stores nothing doesn't claim "All changes saved".
  let used = false;
  let saving = false;
  let error = '';
  const STATUS = {
    synced: 'All changes saved to your account',
    saving: 'Saving…',
    offline: "Offline: changes will sync when you're back online",
    error: () => `Couldn't sync: ${error}`,
  };
  function showStatus() {
    ui.status.hidden = ui.dot.hidden = !used;
    if (!used) {
      ui.button.setAttribute('aria-label', `Menu: ${ui.name.textContent}`);
      ui.button.title = ui.name.textContent;
      return;
    }
    const state = error ? 'error' : !navigator.onLine ? 'offline' : saving ? 'saving' : 'synced';
    const text = typeof STATUS[state] === 'function' ? STATUS[state]() : STATUS[state];
    ui.status.className = `sync-status ${state}`;
    ui.status.replaceChildren(icon({ synced: 'cloud-check', saving: 'cloud-arrow-up', offline: 'cloud-slash', error: 'warning-circle' }[state]), text);
    ui.dot.className = `sync-dot ${state}`;
    ui.button.setAttribute('aria-label', `Menu: ${ui.name.textContent}. ${text}`);
    ui.button.title = text;
  }
  window.AppAccount.setStatus = (s = {}) => {
    used = true;
    if ('saving' in s) saving = !!s.saving;
    if ('error' in s) error = s.error ? (s.error.code === 'permission-denied' ? 'not allowed' : (s.error.code || s.error.message || String(s.error))) : '';
    showStatus();
  };
  addEventListener('online', showStatus);
  addEventListener('offline', showStatus);

  // ---- Signed in / out ----------------------------------------------------
  authLib.onAuthStateChanged(auth, (user) => {
    setMenu(false);
    ui.box.classList.toggle('signed-in', !!user);
    ui.signIn.hidden = !!user;
    ui.signOut.hidden = !user;
    ui.who.hidden = !user;
    window.AppAccount.user = user;
    if (user) {
      localStorage.setItem(SIGNED_IN_KEY, '1');
      const name = user.displayName || user.email || 'Signed in';
      const letter = name.trim().charAt(0).toUpperCase();
      ui.name.textContent = name;
      ui.email.textContent = user.email || '';
      showPhoto(ui.avatarImg, ui.avatar, user.photoURL, letter);
      showPhoto(ui.whoImg, ui.whoLetter, user.photoURL, letter);
      ui.avatar.classList.add('letter');
      error = '';
      showStatus();
    } else {
      ui.avatarImg.hidden = true; ui.avatar.hidden = false;
      ui.avatar.innerHTML = signedOutAvatar; ui.avatar.classList.remove('letter');
      ui.status.hidden = ui.dot.hidden = true;
      ui.button.setAttribute('aria-label', 'Menu'); ui.button.title = 'Menu';
      if (localStorage.getItem(SIGNED_IN_KEY)) toast('Signed out.');
      localStorage.removeItem(SIGNED_IN_KEY);
    }
    window.dispatchEvent(new CustomEvent('account:change', { detail: { user } }));
  });
}

// Short message at the bottom of the screen.
let toastTimer;
function toast(message, ms = 4000) {
  const el = document.getElementById('toast');
  el.textContent = message;
  el.hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { el.hidden = true; }, ms);
}
