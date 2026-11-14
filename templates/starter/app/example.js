// STARTER EXAMPLE: delete this file (and its import in app/main.js) when you
// start building the real app. It shows the usual patterns in one place:
// a component, shared data with signals, a form, a list, an empty state,
// and the style kit's classes and icons.
import { html } from 'htm/preact';
import { useState } from 'preact/hooks';
import { signal, computed } from '@preact/signals';
import { EmptyState } from '../ui.js';

// Shared data: any component that reads a signal re-draws when it changes.
// (Kept in memory only, so the example never leaves anything behind.)
const items = signal([
  { id: 1, text: 'Try ticking this off', done: false },
  { id: 2, text: 'Open the menu and pick an accent colour', done: false },
]);
const filter = signal('all');   // 'all' | 'active' | 'done'
const shown = computed(() => items.value.filter((i) =>
  filter.value === 'all' ? true : filter.value === 'done' ? i.done : !i.done));
const left = computed(() => items.value.filter((i) => !i.done).length);

const add = (text) => { items.value = [...items.value, { id: Date.now(), text, done: false }]; };
const toggle = (id) => { items.value = items.value.map((i) => (i.id === id ? { ...i, done: !i.done } : i)); };
const remove = (id) => { items.value = items.value.filter((i) => i.id !== id); };

// Icons from icons.js (Phosphor Regular) as a small component.
const Icon = ({ name }) => html`<span ref=${(el) => el && !el.firstChild && el.append(icon(name))} />`;

function AddForm() {
  const [text, setText] = useState('');   // local state: only this form needs it
  const [error, setError] = useState('');
  const submit = (e) => {
    e.preventDefault();
    if (!text.trim()) return setError('Type something first.');
    add(text.trim()); setText(''); setError('');
  };
  return html`
    <form class="row example-form" onSubmit=${submit} noValidate>
      <div class="field grow">
        <label for="ex-new" class="visually-hidden">New item</label>
        <input id="ex-new" class="input" placeholder="Add an item…" value=${text}
          aria-invalid=${error ? 'true' : 'false'} aria-describedby="ex-error"
          onInput=${(e) => { setText(e.target.value); setError(''); }} />
      </div>
      <button class="btn primary"><${Icon} name="plus" />Add</button>
      ${error && html`<span id="ex-error" class="error-text full">${error}</span>`}
    </form>`;
}

function Filter() {
  const opts = [['all', 'All'], ['active', 'To do'], ['done', 'Done']];
  return html`
    <div class="seg" role="radiogroup" aria-label="Show">
      ${opts.map(([v, label]) => html`
        <button type="button" role="radio" aria-checked=${filter.value === v} onClick=${() => { filter.value = v; }}>${label}</button>`)}
    </div>`;
}

function Item({ item }) {
  return html`
    <li>
      <label class="check grow">
        <input type="checkbox" checked=${item.done} onChange=${() => toggle(item.id)} />
        <span class=${item.done ? 'done-text' : ''}>${item.text}</span>
      </label>
      <button class="btn ghost icon sm" aria-label=${`Delete "${item.text}"`} onClick=${() => remove(item.id)}><${Icon} name="trash" /></button>
    </li>`;
}

export function Example() {
  return html`
    <section class="card example" aria-labelledby="ex-title">
      <div class="row">
        <h2 id="ex-title" class="grow">Starter example</h2>
        <span class="badge">${left} to do</span>
      </div>
      <div class="notice"><${Icon} name="info" /><div>A small demo of how this app's screens are built.
        Delete <code>app/example.js</code> when you start building. More examples: the style guide.</div></div>
      <${AddForm} />
      <${Filter} />
      ${shown.value.length
        ? html`<ul class="list">${shown.value.map((i) => html`<${Item} key=${i.id} item=${i} />`)}</ul>`
        : html`<${EmptyState} icon="tray" title="Nothing here" text="Add an item above, or pick another filter." />`}
    </section>`;
}
