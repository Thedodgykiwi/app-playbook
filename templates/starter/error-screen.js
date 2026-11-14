// "Something went wrong": if the app fails while it's starting up (a script
// error, a file that didn't load), this covers the page with a friendly screen
// instead of leaving it blank: Try again (reload) and Report a problem (opens
// a pre-filled GitHub issue on the app's repo). Static sites have no server, so
// this replaces a "500" page. Errors after the app is up are left to the app
// (and the browser's console); call AppReady() once the first screen is drawn.
(() => {
  let ready = false, shown = false;
  window.AppReady = () => { ready = true; };

  function show(detail) {
    if (ready || shown) return;
    shown = true;
    const el = document.createElement('div');
    el.className = 'error-screen';
    el.setAttribute('role', 'alert');
    const art = typeof icon === 'function' ? icon('warning-circle-duotone') : document.createElement('span');
    const btn = (label, iconName, cls) => {
      const b = document.createElement(cls === 'a' ? 'a' : 'button');
      b.className = cls === 'a' ? 'btn outline' : 'btn primary';
      if (cls !== 'a') b.type = 'button';
      if (typeof icon === 'function') b.append(icon(iconName));
      b.append(label);
      return b;
    };
    const box = document.createElement('div');
    box.className = 'state';
    const artWrap = document.createElement('div');
    artWrap.className = 'state-art is-error';
    artWrap.setAttribute('aria-hidden', 'true');
    artWrap.append(art);
    const h = document.createElement('h2'); h.textContent = 'Oops, something went wrong';
    const p = document.createElement('p'); p.textContent = "The app couldn't finish loading. Your saved data is safe.";
    const actions = document.createElement('div'); actions.className = 'state-actions';
    const again = btn('Try again', 'arrow-clockwise');
    again.addEventListener('click', () => location.reload());
    actions.append(again);
    // Report a problem: a pre-filled issue on the app's GitHub repo (<user>.github.io/<repo>/…).
    const user = location.hostname.endsWith('.github.io') ? location.hostname.split('.')[0] : null;
    const repo = location.pathname.split('/').filter(Boolean)[0];
    if (user && repo) {
      const report = btn('Report a problem', 'bug', 'a');
      const body = `**What's happening**\nThe app showed "Something went wrong" while loading.\n\n**Where**\n${location.href}\n${navigator.userAgent}\n\n**Expected**\nThe app loads.\n\n**Reported by**\nUs\n\n**Notes**\nError: ${String(detail).slice(0, 300)}`;
      report.href = `https://github.com/${user}/${repo}/issues/new?labels=bug&title=${encodeURIComponent('App shows "Something went wrong" while loading')}&body=${encodeURIComponent(body)}`;
      report.target = '_blank'; report.rel = 'noopener';
      actions.append(report);
    }
    box.append(artWrap, h, p, actions);
    el.append(box);
    document.body.append(el);
    again.focus();
  }

  // Script errors, and files (scripts, styles) that failed to load.
  addEventListener('error', (e) => {
    const t = e.target;
    if (t && t !== window && (t.tagName === 'SCRIPT' || (t.tagName === 'LINK' && t.rel === 'stylesheet'))) show(`Couldn't load ${t.src || t.href}`);
    else if (e.error || e.message) show(e.message || e.error);
  }, true);
  addEventListener('unhandledrejection', (e) => show(e.reason?.message || e.reason));
  window.AppError = { preview: () => { const r = ready; ready = false; shown = false; show('preview'); ready = r; } };   // style guide demo
})();
