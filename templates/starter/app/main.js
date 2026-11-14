// {{APP_NAME}}: the app's screens.
// Built with Preact + htm: React-style components that run straight in the
// browser (no build step). The libraries live in vendor/ and are named in the
// import map in index.html. Patterns: playbook guides/preact.md; live
// examples: styleguide.html ("Components" section).
import { html, render } from 'htm/preact';

// ---- Starter example: delete this import and app/example.js when you start building ----
import { Example } from './example.js';

function App() {
  // Replace this with the app's own screens, e.g. html`<${TaskList} />`.
  return html`<${Example} />`;
}

render(html`<${App} />`, document.getElementById('app'));
window.AppReady?.();   // the app is up: no "Something went wrong" screen from now on (error-screen.js)
