// Makes an app's home-screen / favicon images for every stage, into
// <app-repo>/icons/app/<stage>/ (one colour per stage, white glyph).
// Shared by every app (one copy, in the playbook). Needs Node + Playwright and
// the Phosphor icons package unpacked somewhere (npm pack @phosphor-icons/core).
//
//   node tools/make-app-icons.js --phosphor <dir>/package --glyph squares-four \
//        [--weight bold] --out <app-repo>/icons/app
//
// --glyph: any Phosphor icon name (see phosphoricons.com). --weight: regular,
// bold (default: reads well small), fill or duotone. After changing icons on a
// phone, delete and re-add the Home Screen shortcut (iOS keeps the old one).
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const args = Object.fromEntries(process.argv.slice(2).reduce((a, v, i, all) =>
  (v.startsWith('--') ? a.concat([[v.slice(2), all[i + 1]]]) : a), []));
const { phosphor, glyph = 'squares-four', weight = 'bold', out } = args;
if (!phosphor || !out) {
  console.error('Usage: node make-app-icons.js --phosphor <@phosphor-icons/core package dir> --glyph <name> [--weight bold] --out <app>/icons/app');
  process.exit(1);
}
// Stage colours: gradient top-left → bottom-right (match the deploy's stage colours).
const STAGES = {
  main:    ['#4c6ef5', '#364fc7'],
  staging: ['#f08c00', '#d9480f'],
  alpha:   ['#d6336c', '#a61e4d'],
  dev:     ['#7950f2', '#5f3dc4'],
  local:   ['#6c757d', '#343a40'],
};
const file = weight === 'regular' ? `${glyph}.svg` : `${glyph}-${weight}.svg`;
const inner = fs.readFileSync(path.join(phosphor, 'assets', weight, file), 'utf8')
  .match(/<svg[^>]*>([\s\S]*)<\/svg>/)[1].replace(/<rect width="256" height="256" fill="none"\s*\/>/, '');

// rounded: transparent corners (browser tab icons only). Home-screen icons are
// full-bleed squares: phones apply their own shape, and some mishandle transparency.
function svg({ from, to, rounded, glyphScale }) {
  const r = rounded ? 56 : 0, g = 256 * glyphScale, o = (256 - g) / 2;
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256">
  <defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="${from}"/><stop offset="1" stop-color="${to}"/></linearGradient></defs>
  <rect width="256" height="256" rx="${r}" fill="url(#bg)"/>
  <svg x="${o}" y="${o}" width="${g}" height="${g}" viewBox="0 0 256 256" fill="#fff">${inner}</svg>
</svg>`;
}

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  for (const [stage, [from, to]] of Object.entries(STAGES)) {
    const dir = path.join(out, stage);
    fs.mkdirSync(dir, { recursive: true });
    const outputs = [
      ['favicon.svg', null, { rounded: true, glyphScale: 0.66 }],
      ['favicon-32.png', 32, { rounded: true, glyphScale: 0.70 }],
      ['icon-192.png', 192, { rounded: false, glyphScale: 0.58 }],
      ['icon-512.png', 512, { rounded: false, glyphScale: 0.58 }],
      ['icon-maskable-512.png', 512, { rounded: false, glyphScale: 0.50 }], // inside the safe zone
      ['apple-touch-icon.png', 180, { rounded: false, glyphScale: 0.58 }],
    ];
    for (const [name, size, opts] of outputs) {
      const markup = svg({ from, to, ...opts });
      if (!size) { fs.writeFileSync(path.join(dir, name), markup + '\n'); continue; }
      await page.setViewportSize({ width: size, height: size });
      await page.setContent(`<style>html,body{margin:0;background:transparent}svg{display:block;width:${size}px;height:${size}px}</style>${markup}`);
      await page.screenshot({ path: path.join(dir, name), omitBackground: true });
    }
    console.log('made', stage);
  }
  await browser.close();
})();
