// {{APP_NAME}}: app code goes here.
//
// The stage this copy is running on: 'local', 'dev', 'alpha', 'staging' or
// 'main' (Production). Set per stage by the deploy (stage.js).
const stage = window.STAGE || 'local';

// All stages share one web address, so anything saved in the browser must be
// kept separate per stage, e.g.:
//   const storageKey = `my-data-${stage}`;
//
// Signed in or out (only once Google sign-in is switched on; see account.js):
//   window.addEventListener('account:change', (e) => { const user = e.detail.user; });
