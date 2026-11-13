// {{APP_NAME}}: app code goes here.
// The starter only wires up the parts every app shares: the stage banner,
// the build label and the Pipeline link. Anything saved in the browser must
// be keyed per stage (all stages share one web address), e.g.:
//   const storageKey = `my-data-${stage}`;

const stage = window.STAGE || 'local';
document.getElementById('build').textContent = stage;

// Stage banner on every stage except Production, so test versions can't be mistaken for it.
if (stage !== 'main') {
  const banner = document.getElementById('stage-banner');
  banner.textContent = `${stage.toUpperCase()} environment`;
  banner.className = `stage-${stage}`;
  banner.hidden = false;
}

// The pipeline page lives once, at the site root (…/<repo>/pipeline/).
const pipelineLink = document.getElementById('pipeline-link');
if (stage !== 'local') {
  pipelineLink.href = stage === 'main' ? 'pipeline/' : '../pipeline/';
  pipelineLink.hidden = false;
}

// Signed in or out (only once Firebase sign-in is switched on; see account.js):
//   window.addEventListener('account:change', (e) => { const user = e.detail.user; ... });
