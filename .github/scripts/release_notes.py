#!/usr/bin/env python3
"""Build releases.json for one stage from its git history.

Usage: release_notes.py <repo_dir> <stage> <output.json>

Promoted stages (alpha, staging, main) list each promotion into them, using
the release notes the promote skill writes into the merge commit. Pull
request merges done on GitHub are listed too. Dev has no promotions, so it
lists its most recent changes instead.

A bullet that came from a GitHub issue ends with "(#12)". For those, the
issue's type label (name and colour) is looked up and saved under "issues"
so the app can show a small coloured pill such as "tweak #12" (reference
only, not a link). Needs GITHUB_REPOSITORY (and GH_TOKEN, optional for
public repos); if the lookup fails, the app shows a plain "#12" pill.
"""
import json
import os
import re
import subprocess
import sys
import urllib.request

# Which label names the pill, in order of preference (priority labels never do).
TYPE_LABELS = ["bug", "feature", "tweak", "performance"]
ISSUE_PILL = re.compile(r"\(#(\d+)\)")

FS, RS = "\x1f", "\x1e"


def git(repo, *args):
    return subprocess.run(["git", "-C", repo, *args], capture_output=True,
                          text=True, check=True).stdout


def bullets_from_changes(text):
    """'  abc1234 Subject (Author)' lines -> '- Subject' bullets."""
    out = []
    for line in text.splitlines():
        m = re.match(r"\s*[0-9a-f]{7,}\s+(.*?)(?:\s+\([^)]*\))?\s*$", line)
        if m:
            out.append(f"- {m.group(1)}")
    return "\n".join(out)


def promotions(repo):
    log = git(repo, "log", "--first-parent", "--merges", "-n", "50",
              f"--format=%h{FS}%cI{FS}%B{RS}")
    releases = []
    for entry in log.split(RS):
        entry = entry.strip("\n")
        if not entry:
            continue
        sha, date, body = entry.split(FS, 2)
        subject, _, rest = body.strip().partition("\n")
        rest = rest.strip()
        promo = re.match(r"Promote (\w+) → (\w+)", subject)
        pr = re.match(r"Merge pull request #(\d+) from \S+?/(\S+)", subject)
        if promo:
            notes = ""
            if "Release notes:" in rest:
                notes = rest.split("Release notes:", 1)[1]
                notes = notes.split("Changes included:", 1)[0].strip()
            if not notes and "Changes included:" in rest:
                notes = bullets_from_changes(rest.split("Changes included:", 1)[1])
            releases.append({"sha": sha, "date": date, "from": promo.group(1),
                             "notes": notes or "- Minor updates"})
        elif pr:
            lines = [l.strip() for l in rest.splitlines() if l.strip()]
            notes = "\n".join(f"- {l}" for l in lines) or "- Minor updates"
            releases.append({"sha": sha, "date": date, "from": pr.group(2),
                             "pr": int(pr.group(1)), "notes": notes})
    return releases


def recent_changes(repo):
    log = git(repo, "log", "--no-merges", "-n", "15", f"--format=%h{FS}%cI{FS}%s")
    return [dict(zip(("sha", "date", "title"), l.split(FS, 2)))
            for l in log.splitlines() if l]


def issue_labels(notes_texts):
    """{"12": {"label": "tweak", "color": "c5def5"}} for every "(#12)" in the notes."""
    slug = os.environ.get("GITHUB_REPOSITORY")
    nums = sorted({n for t in notes_texts for n in ISSUE_PILL.findall(t)}, key=int)
    if not slug or not nums:
        return {}
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "app-playbook-deploy"}
    if os.environ.get("GH_TOKEN"):
        headers["Authorization"] = f"Bearer {os.environ['GH_TOKEN']}"
    out = {}
    for n in nums:
        try:
            req = urllib.request.Request(f"https://api.github.com/repos/{slug}/issues/{n}", headers=headers)
            labels = json.load(urllib.request.urlopen(req, timeout=10)).get("labels", [])
        except Exception as e:                    # offline, rate-limited, not found...
            print(f"  (couldn't look up issue #{n}: {e})")
            continue
        by_name = {l["name"]: l for l in labels}
        pick = next((by_name[t] for t in TYPE_LABELS if t in by_name), None) or next(
            (l for l in labels if not l["name"].startswith("priority")), None)
        if pick:
            out[n] = {"label": pick["name"], "color": pick["color"]}
    return out


def main():
    repo, stage, out = sys.argv[1:4]
    data = {"stage": stage, "releases": [], "recent": []}
    if stage == "dev":
        data["recent"] = recent_changes(repo)
    else:
        data["releases"] = promotions(repo)
        data["issues"] = issue_labels(r["notes"] for r in data["releases"])
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"{stage}: {len(data['releases'])} release(s), {len(data['recent'])} recent change(s)")


if __name__ == "__main__":
    main()
