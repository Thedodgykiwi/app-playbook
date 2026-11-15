// Firebase web app settings (used by account.js). Not secret: every Firebase
// web app ships them to the browser; data is protected by firestore.rules.
// While this is null, sign-in is switched off and nothing talks to Firebase.
// To switch sign-in on, follow the playbook's firebase-auth-and-firestore.md.
window.FIREBASE_CONFIG = null;

// "Report issue" button on the test stages' banner (playbook report-issue.md).
// Needs sign-in on, the issueReports rules, a testers list and the GitHub
// secrets; switch on only once those are set up.
window.REPORT_ISSUES = false;
