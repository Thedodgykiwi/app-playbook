// Compare mode + stage switcher (shared; the deploy adds this to every stage
// right after stage.js, so it knows window.STAGE). Playbook: guides/compare-stages.md.
//
// Normal mode (no "?compare" in the address): does nothing except turn the
// stage banner's name into a small menu to hop to the same app on another
// stage. Production has no banner, so nothing at all changes there.
//
// Compare mode ("?compare"): every stage reads and writes ONE shared set of
// data in this browser instead of its own. Any storage key ending in
// "-<stage>" or ":<stage>" (the starter's convention, e.g. "todos-dev") is
// read and written as "...-compare" / "...:compare" instead. Sign-in and cloud
// sync are switched off, so nothing is ever written to an account. The first
// time, the list is filled from the app's own compare-sample.json (optional).
// "&theme=light|dark" forces a theme (used by the Pipeline page's Compare tab).
(function () {
  'use strict';
  var STAGE = window.STAGE || 'local';
  var params = new URLSearchParams(location.search);
  var COLORS = { main: '__C_MAIN__', staging: '__C_STAGING__', alpha: '__C_ALPHA__', dev: '__C_DEV__' };
  var NAMES = { main: 'Production', staging: 'Staging', alpha: 'Alpha', dev: 'Dev', local: 'Local' };
  var ORDER = ['dev', 'alpha', 'staging', 'main'];
  var compare = params.has('compare') && STAGE !== 'local';

  if (compare) {
    window.COMPARE = true;
    // Never sync: hide the Firebase settings from the app, whatever loads later.
    try { Object.defineProperty(window, 'FIREBASE_CONFIG', { get: function () { return null; }, set: function () {}, configurable: false }); } catch (e) {}
    var real = { get: Storage.prototype.getItem, set: Storage.prototype.setItem, remove: Storage.prototype.removeItem };
    var suffix = new RegExp('([-:])' + STAGE.replace(/[^a-z]/g, '') + '$');
    var blocked = /^(signed-in|cloud-copy-)/;
    var map = function (k) { return String(k).replace(suffix, '$1compare'); };
    Storage.prototype.getItem = function (k) { return blocked.test(k) ? null : real.get.call(this, map(k)); };
    Storage.prototype.setItem = function (k, v) { if (!blocked.test(k)) real.set.call(this, map(k), v); };
    Storage.prototype.removeItem = function (k) { if (!blocked.test(k)) real.remove.call(this, map(k)); };

    // Sample data: compare-sample.json = { "key": "todos", "items": [...] }.
    // "@today", "@today+1", "@today-2" become dates; "@now-2h", "@now-3d" times.
    var sample = null;
    try {
      var x = new XMLHttpRequest();
      x.open('GET', 'compare-sample.json', false);   // tiny file, needed before the app reads its data
      x.send();
      if (x.status === 200) sample = JSON.parse(x.responseText);
    } catch (e) { sample = null; }
    var day = function (n) { var d = new Date(); d.setDate(d.getDate() + n); return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0'); };
    var resolve = function (v) {
      if (Array.isArray(v)) return v.map(resolve);
      if (v && typeof v === 'object') { var o = {}; Object.keys(v).forEach(function (k) { o[k] = resolve(v[k]); }); return o; }
      if (typeof v !== 'string') return v;
      var m = v.match(/^@today([+-]\d+)?$/); if (m) return day(+(m[1] || 0));
      m = v.match(/^@now(?:([+-]\d+)([hd]))?$/); if (m) return Date.now() + (+(m[1] || 0)) * (m[2] === 'd' ? 864e5 : 36e5);
      return v;
    };
    var listKey = sample && sample.key ? sample.key + '-compare' : null;
    window.compareReset = function () {
      if (listKey) real.set.call(localStorage, listKey, JSON.stringify(resolve(sample.items || [])));
      location.reload();
    };
    if (listKey && real.get.call(localStorage, listKey) === null) real.set.call(localStorage, listKey, JSON.stringify(resolve(sample.items || [])));
    // Another stage (another window) changed the shared data: show it here too.
    // Only when the content really changed: each stage saves its copy on load,
    // perhaps with its details in a different order, which must not set off a
    // chain of reloads between windows.
    var canon = function (t) {
      try {
        var walk = function (v) {
          if (Array.isArray(v)) return v.map(walk);
          if (v && typeof v === 'object') { var o = {}; Object.keys(v).sort().forEach(function (k) { if (v[k] !== null && v[k] !== undefined && v[k] !== false && !(Array.isArray(v[k]) && !v[k].length)) o[k] = walk(v[k]); }); return o; }
          return v;
        };
        return JSON.stringify(walk(JSON.parse(t)));
      } catch (e) { return t; }
    };
    var pending = 0;
    addEventListener('storage', function (e) {
      // Only the app's own list (from compare-sample.json): housekeeping values such as
      // "which hint was shown" change on every load and must not trigger reloads.
      if (!listKey || e.key !== listKey || canon(e.oldValue) === canon(e.newValue)) return;
      clearTimeout(pending); pending = setTimeout(function () { location.reload(); }, 150);
    });
    window.COMPARE_READY = true;   // the Pipeline page's Compare tab checks this
  }

  var css = function (text) { var s = document.createElement('style'); s.textContent = text; document.head.appendChild(s); };
  var hrefFor = function (to) {
    var base = STAGE === 'main' ? './' : '../';
    return base + (to === 'main' ? '' : to + '/') + (compare ? location.search : '');
  };

  var setup = function () {
    var theme = params.get('theme');
    if (compare && (theme === 'light' || theme === 'dark')) document.documentElement.dataset.theme = theme;
    var banner = document.getElementById('stage-banner'), name = document.getElementById('stage-name');
    if (!banner || !name || banner.dataset.switcher) return;
    if (compare) {
      if (banner.hidden) {   // Production: show a banner while comparing, in its own colour
        banner.hidden = false;
        banner.style.background = COLORS.main.charAt(0) === '#' ? COLORS.main : '#3b5bdb';
        document.body.classList.add('has-banner');
      }
      name.textContent = (NAMES[STAGE] || STAGE) + ' · compare';
      ['report-link', 'pipeline-link'].forEach(function (id) { var el = document.getElementById(id); if (el) el.style.display = 'none'; });
      var r = document.createElement('button');
      r.type = 'button'; r.className = 'compare-reset'; r.textContent = 'Reset';
      r.title = 'Put the sample list back';
      r.onclick = function () { window.compareReset(); };
      banner.appendChild(r);
    }
    if (banner.hidden || STAGE === 'local') return;
    banner.dataset.switcher = '1';
    // Stage switcher: tap the stage name for a menu of the other stages.
    var btn = document.createElement('button');
    btn.type = 'button'; btn.className = 'stage-switch';
    btn.setAttribute('aria-haspopup', 'menu'); btn.setAttribute('aria-expanded', 'false');
    btn.setAttribute('aria-label', name.textContent + ': switch stage');
    name.parentNode.replaceChild(btn, name); btn.appendChild(name);
    btn.insertAdjacentHTML('beforeend', '<svg width="12" height="12" viewBox="0 0 256 256" aria-hidden="true"><path d="M48 96l80 80 80-80" fill="none" stroke="currentColor" stroke-width="28" stroke-linecap="round" stroke-linejoin="round"/></svg>');
    var menu = document.createElement('div');
    menu.className = 'stage-menu'; menu.setAttribute('role', 'menu'); menu.hidden = true;
    menu.innerHTML = ORDER.map(function (k) {
      var here = k === STAGE, c = COLORS[k].charAt(0) === '#' ? COLORS[k] : '#868e96';
      return '<a role="menuitem" href="' + hrefFor(k) + '"' + (here ? ' aria-current="page"' : '') + '><span style="background:' + c + '"></span>' + NAMES[k] + (here ? ' <em>(here)</em>' : '') + '</a>';
    }).join('');
    document.body.appendChild(menu);
    var close = function () { menu.hidden = true; btn.setAttribute('aria-expanded', 'false'); };
    btn.addEventListener('click', function (e) {
      e.stopPropagation();
      var b = btn.getBoundingClientRect();
      menu.style.top = (b.bottom + 6) + 'px';
      menu.hidden = !menu.hidden;
      btn.setAttribute('aria-expanded', String(!menu.hidden));
      if (!menu.hidden) { var first = menu.querySelector('a:not([aria-current])'); if (first) first.focus(); }
    });
    addEventListener('click', function (e) { if (!menu.contains(e.target)) close(); });
    addEventListener('keydown', function (e) { if (e.key === 'Escape' && !menu.hidden) { close(); btn.focus(); } });
    css('.stage-switch{display:inline-flex;align-items:center;gap:.35rem;font:inherit;color:inherit;letter-spacing:inherit;background:rgba(255,255,255,.16);border:0;border-radius:99px;padding:.15rem .65rem;min-height:28px;cursor:pointer}' +
      '.stage-switch::before{content:"";position:absolute;inset:-8px 0}.stage-switch{position:relative}' +
      '.stage-menu{position:fixed;left:50%;transform:translateX(-50%);z-index:80;min-width:12.5rem;background:#fff;color:#1d1f23;border-radius:14px;box-shadow:0 10px 30px rgba(0,0,0,.22);padding:.35rem;font:500 .95rem system-ui,-apple-system,sans-serif}' +
      '.stage-menu a{display:flex;align-items:center;gap:.6rem;min-height:44px;padding:0 .75rem;border-radius:10px;color:inherit;text-decoration:none}' +
      '.stage-menu a:hover,.stage-menu a:focus-visible{background:#f1f3f5;outline:none}' +
      '.stage-menu a span{width:.75rem;height:.75rem;border-radius:50%;flex:none}.stage-menu em{color:#6c757d;font-style:normal;font-size:.85rem}.stage-menu[hidden]{display:none}' +
      '.compare-reset{position:absolute;right:.6rem;top:50%;transform:translateY(-50%);font:600 .75rem system-ui,-apple-system,sans-serif;color:#fff;background:rgba(255,255,255,.2);border:0;border-radius:99px;padding:.3rem .75rem;cursor:pointer}');
  };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', setup); else setup();
})();
