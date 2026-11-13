# {{APP_NAME}}

{{DESCRIPTION}}

A static web app (plain HTML/CSS/JS, no build step) hosted on GitHub Pages,
released through stages: Dev → Alpha → Staging → Production.

| Stage | Address |
|---|---|
| Dev | https://{{OWNER_LC}}.github.io/{{REPO}}/dev/ |
| Alpha | https://{{OWNER_LC}}.github.io/{{REPO}}/alpha/ |
| Staging | https://{{OWNER_LC}}.github.io/{{REPO}}/staging/ |
| Production | https://{{OWNER_LC}}.github.io/{{REPO}}/ |
| Pipeline (what's where) | https://{{OWNER_LC}}.github.io/{{REPO}}/pipeline/ |

Set up from the app starter in [app-playbook](https://github.com/Thedodgykiwi/app-playbook),
which also provides the shared deploy and the promote skill.

Run locally: `python3 -m http.server 8080` and open http://localhost:8080.
