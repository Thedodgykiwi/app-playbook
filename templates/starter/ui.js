// Ready-made pieces for app screens (Preact + htm). Import what you need:
//   import { EmptyState, SkeletonRows, SkeletonCard, SkeletonTable } from '../ui.js';
//
//   html`<${EmptyState} icon="tray" title="Nothing here yet"
//          text="Your to-dos will show up here once you add one."
//          action=${{ label: 'Add a to-do', icon: 'plus', onClick: focusInput }} />`
//   html`${loading ? html`<${SkeletonRows} count=${4} />` : html`<${List} />`}`
//
// Live examples: the style guide ("Empty and loading"). Style: big illustration
// on a soft colour blob ("C" from the mock-up).
import { html } from 'htm/preact';

// Icon from icons.js inside a component. The big illustrations use "<name>-duotone".
export const Icon = ({ name, cls = '' }) => html`<span class="icon-wrap" ref=${(el) => {
  if (el && el.dataset.n !== name + cls) { el.replaceChildren(icon(name, cls)); el.dataset.n = name + cls; }
}} />`;

// Empty state: illustration, headline, short explanation, optional action button.
export function EmptyState({ icon: name = 'tray', title, text, action, error = false }) {
  const art = icons.has(`${name}-duotone`) ? `${name}-duotone` : name;
  return html`
    <div class="state" role=${error ? 'alert' : null}>
      <div class=${`state-art${error ? ' is-error' : ''}`} aria-hidden="true"><${Icon} name=${art} /></div>
      ${title && html`<h3>${title}</h3>`}
      ${text && html`<p>${text}</p>`}
      ${action && html`<button type="button" class="btn primary" onClick=${action.onClick}>
        ${action.icon && html`<${Icon} name=${action.icon} />`}${action.label}</button>`}
    </div>`;
}
// icons.js's ICON_PATHS is a global (classic script), visible here.
const icons = { has: (n) => typeof ICON_PATHS !== 'undefined' && !!ICON_PATHS[n] };

// Loading skeletons: grey shimmering shapes where content is about to appear.
const widths = ['72%', '55%', '64%', '48%', '68%'];
export const SkeletonRows = ({ count = 3 }) => html`
  <div class="sk-rows" aria-busy="true" aria-label="Loading">
    ${Array.from({ length: count }, (_, i) => html`
      <div class="sk-row"><span class="skeleton" /><span class="skeleton" style=${`width:${widths[i % widths.length]}`} /></div>`)}
  </div>`;
export const SkeletonCard = () => html`
  <div class="card sk-card" aria-busy="true" aria-label="Loading">
    <span class="skeleton" style="width:45%;height:.9rem" /><span class="skeleton" style="width:90%" />
    <span class="skeleton" style="width:75%" />
    <div class="row"><span class="skeleton" style="width:4.5rem;height:1.8rem" /><span class="skeleton" style="width:3.8rem;height:1.8rem" /></div>
  </div>`;
export const SkeletonTable = ({ rows = 3, cols = 3 }) => html`
  <div class="sk-table" aria-busy="true" aria-label="Loading">
    ${Array.from({ length: rows }, () => html`
      <div style=${`grid-template-columns: 2fr ${'1fr '.repeat(cols - 1)}`}>
        ${Array.from({ length: cols }, (_, c) => html`<span class="skeleton" style=${`width:${c ? 55 : 80}%`} />`)}
      </div>`)}
  </div>`;
