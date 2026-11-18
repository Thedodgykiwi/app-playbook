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
//   window.AppAccount.dataCollections = ['todos']   // what "Download my data" / "Delete my account" cover, on every stage
//   window.addEventListener('account:deleted', ...)  // clear any copies the app keeps on the device
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
    status: $('sync-status'), signOut: $('sign-out'), label: $('avatar-label'),
  };
  // The menu itself (open/close, Settings, version) is menu.js.
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

  // ---- Download my data (Settings → Your account) ---------------------------
  // A copy of everything in the account, every stage, as a JSON file (the right to
  // a copy of your data). Dates come out as ISO text.
  $('download-data')?.addEventListener('click', async (e) => {
    const user = auth.currentUser, btn = e.currentTarget; if (!user) return;
    btn.disabled = true;
    // Firestore dates → readable text (before JSON, which would turn them into {seconds, …}).
    const plain = (v) => (v && typeof v.toDate === 'function' ? v.toDate().toISOString()
      : Array.isArray(v) ? v.map(plain) : v && typeof v === 'object' ? Object.fromEntries(Object.entries(v).map(([k, x]) => [k, plain(x)])) : v);
    try {
      const out = { app: document.title, exportedAt: new Date().toISOString(),
        account: { name: user.displayName, email: user.email }, stages: {} };
      for (const stage of ['local', 'dev', 'alpha', 'staging', 'main']) {
        for (const name of window.AppAccount.dataCollections || []) {
          const snap = await fs.getDocs(fs.collection(db, 'users', user.uid, 'stages', stage, name));
          if (!snap.size) continue;
          (out.stages[stage] ||= {})[name] = snap.docs.map((d) => ({ id: d.id, ...plain(d.data()) }));
        }
      }
      const json = JSON.stringify(out, null, 2);
      const a = Object.assign(document.createElement('a'), {
        href: URL.createObjectURL(new Blob([json], { type: 'application/json' })),
        download: `${(document.title || 'app').toLowerCase().replace(/[^a-z0-9]+/g, '-')}-my-data-${new Date().toISOString().slice(0, 10)}.json`,
      });
      document.body.append(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(a.href), 10000);
      toast('Your data has been downloaded.');
    } catch (err) {
      toast(`Couldn't download your data (${err.code || err.message}).`, 6000);
    } finally { btn.disabled = false; }
  });

  // ---- Delete my account (Settings → Your account) --------------------------
  // Removes everything the app saved for this person on every stage (the app lists
  // its collections in AppAccount.dataCollections), then the sign-in itself. Google
  // may ask them to sign in again first (it only deletes after a recent sign-in).
  let deleting = false;
  const delDlg = $('delete-account'), delGo = $('delete-account-go'), delErr = $('delete-account-error');
  $('delete-account-open')?.addEventListener('click', () => { $('settings')?.close(); delErr.hidden = true; delDlg.showModal(); });
  delGo?.addEventListener('click', async () => {
    const user = auth.currentUser; if (!user) return;
    delGo.disabled = true; delGo.textContent = 'Deleting…'; delErr.hidden = true;
    try {
      for (const stage of ['local', 'dev', 'alpha', 'staging', 'main']) {
        for (const name of window.AppAccount.dataCollections || []) {
          const snap = await fs.getDocs(fs.collection(db, 'users', user.uid, 'stages', stage, name));
          for (let i = 0; i < snap.docs.length; i += 400) {   // batches hold up to 500 writes
            const batch = fs.writeBatch(db);
            snap.docs.slice(i, i + 400).forEach((d) => batch.delete(d.ref));
            await batch.commit();
          }
        }
      }
      deleting = true;
      try { await authLib.deleteUser(user); } catch (err) {
        if (err.code !== 'auth/requires-recent-login') throw err;
        await authLib.reauthenticateWithPopup(user, new authLib.GoogleAuthProvider());
        await authLib.deleteUser(user);
      }
      delDlg.close();
      window.dispatchEvent(new CustomEvent('account:deleted'));
      toast('Your account has been deleted.', 6000);
    } catch (err) {
      deleting = false;
      delErr.textContent = ['auth/popup-closed-by-user', 'auth/cancelled-popup-request'].includes(err.code)
        ? "Not deleted: the sign-in check was closed. Try again when you're ready."
        : `Couldn't finish deleting (${err.code || err.message}). Check your connection and try again.`;
      delErr.hidden = false;
    } finally { delGo.disabled = false; delGo.textContent = 'Delete my account'; }
  });

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
    document.getElementById('signin-box').hidden = !!user;   // sign-in lives at the top of the menu
    ui.signOut.hidden = !user;
    const acct = $('account-setting'); if (acct) acct.hidden = !user;
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
      ui.label.textContent = 'My account';
      error = '';
      showStatus();
    } else {
      ui.avatarImg.hidden = true; ui.avatar.hidden = false;
      ui.avatar.innerHTML = signedOutAvatar; ui.avatar.classList.remove('letter');
      ui.label.textContent = 'Menu';
      ui.status.hidden = ui.dot.hidden = true;
      ui.button.setAttribute('aria-label', 'Menu'); ui.button.title = 'Menu';
      if (localStorage.getItem(SIGNED_IN_KEY) && !deleting) toast('Signed out.');
      localStorage.removeItem(SIGNED_IN_KEY);
    }
    window.dispatchEvent(new CustomEvent('account:change', { detail: { user } }));
  });
}

// Short message at the bottom of the screen (toast.js).
const toast = (message, ms) => window.AppToast?.show(message, { duration: ms });
