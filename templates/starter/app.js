// {{APP_NAME}}: app code goes here.
//
// The stage this copy is running on: 'local', 'dev', 'alpha', 'staging' or
// 'main' (Production). Set per stage by the deploy (stage.js).
const stage = window.STAGE || 'local';

// Stage banner on every stage except Production, with a link to the pipeline
// page (built by the shared deploy at the site root; not on local copies).
if (stage !== 'main') {
  const banner = document.getElementById('stage-banner');
  document.getElementById('stage-name').textContent = `${stage.toUpperCase()} environment`;
  banner.className = `stage-${stage}`;
  banner.hidden = false;
  document.body.classList.add('has-banner');
  if (stage !== 'local') document.getElementById('pipeline-link').hidden = false;
}

// All stages share one web address, so anything saved in the browser must be
// kept separate per stage, e.g.:
//   const storageKey = `my-data-${stage}`;
//
// Signed in or out (only once Google sign-in is switched on; see account.js):
//   window.addEventListener('account:change', (e) => { const user = e.detail.user; });
