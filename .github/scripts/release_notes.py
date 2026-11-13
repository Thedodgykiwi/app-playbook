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


def promotions(repo, limit=50, ref="HEAD"):
    log = git(repo, "log", "--first-parent", "--merges", *(["-n", str(limit)] if limit else []),
              f"--format=%h{FS}%cI{FS}%B{RS}", ref)
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


def release_names(repo, tz_name=None, ref="HEAD"):
    """{full commit sha: "v2026.11.13.2"} for every Production release on main.

    The ONE place release names are decided (used for GitHub releases and for
    the version shown in "What's new"): the date of the release (RELEASE_TZ,
    default UTC) plus its position that day: 1st -> v2026.11.13, 2nd ->
    v2026.11.13.2 ... Worked out from history, so it never depends on which
    tags or GitHub releases happen to exist."""
    from datetime import datetime
    from zoneinfo import ZoneInfo
    tz = ZoneInfo(tz_name or os.environ.get("RELEASE_TZ") or "UTC")
    per_day, names = {}, {}
    for r in reversed(promotions(repo, limit=None, ref=ref)):  # oldest first, whole history
        full = git(repo, "rev-parse", r["sha"]).strip()
        day = datetime.fromisoformat(r["date"]).astimezone(tz).strftime("%Y.%m.%d")
        per_day[day] = per_day.get(day, 0) + 1
        n = per_day[day]
        names[full] = f"v{day}" if n == 1 else f"v{day}.{n}"
    return names


def rollbacks(repo, ref="HEAD"):
    """Emergency rollbacks of Production ("Roll back Production: ..." commits on
    main, made by the promote skill's rollback command)."""
    log = git(repo, "log", "--first-parent", "--no-merges", "-n", "50",
              f"--format=%H{FS}%cI{FS}%B{RS}", ref)
    out = []
    for entry in log.split(RS):
        entry = entry.strip("\n")
        if not entry:
            continue
        sha, date, body = entry.split(FS, 2)
        if not body.startswith("Roll back Production"):
            continue
        m = re.search(r"^Rolled-back-commit: ([0-9a-f]{40})", body, re.M)
        t = re.search(r"^Rolled-back-release: (\S+)", body, re.M)
        out.append({"sha": sha, "date": date, "body": body,
                    "rolled_back_commit": m.group(1) if m else None,
                    "rolled_back_release": t.group(1) if t and t.group(1) != "none" else None})
    return out


def is_housekeeping(files):
    """Commits that only touch issue screenshots/workflows (.github/) or
    documents (*.md) don't change the app, so Dev doesn't list them."""
    return bool(files) and all(f.startswith(".github/") or f.endswith(".md") for f in files)


COMMIT_ISSUE = re.compile(r"\b(?:issues?|fix(?:es|ed)?|close[sd]?|resolve[sd]?)\s*:?\s*#(\d+)", re.I)


def commit_issues(message):
    """Issue numbers a commit message mentions, including "Issue #3, #4" lists."""
    nums = []
    for line in message.splitlines():
        if COMMIT_ISSUE.search(line):
            nums += [int(n) for n in re.findall(r"#(\d+)", line) if int(n) not in nums]
    return nums


def recent_changes(repo, limit=200):   # older days fold away in "What's new", so keep plenty
    log = git(repo, "log", "--no-merges", "-n", "600", "--name-only",
              f"--format={RS}%h{FS}%cI{FS}%s")
    out = []
    for entry in log.split(RS):
        lines = [l for l in entry.strip("\n").splitlines() if l.strip()]
        if not lines:
            continue
        sha, date, title = lines[0].split(FS, 2)
        if is_housekeeping(lines[1:]):
            continue
        item = {"sha": sha, "date": date, "title": title}
        # Issues the change mentions ("Issue #12", "Fixes #3, #4"), for Dev's pills.
        nums = commit_issues(git(repo, "show", "-s", "--format=%B", sha))
        if nums:
            item["issues"] = nums
        out.append(item)
        if len(out) == limit:
            break
    return out


def issue_labels(notes_texts, numbers=()):
    """{"12": {"label": "tweak", "color": "c5def5"}} for every "(#12)" in the notes
    (plus any extra issue numbers passed in `numbers`)."""
    slug = os.environ.get("GITHUB_REPOSITORY")
    nums = sorted({n for t in notes_texts for n in ISSUE_PILL.findall(t)} | {str(n) for n in numbers}, key=int)
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
        # Type and colour of the issues they mention (Dev's pills and emoji).
        data["issues"] = issue_labels([], [n for c in data["recent"] for n in c.get("issues", [])])
    else:
        releases = promotions(repo)
        if stage == "main":                       # Production releases have version names
            names = release_names(repo)
            for r in releases:
                r["version"] = names.get(git(repo, "rev-parse", r["sha"]).strip())
        rbs = rollbacks(repo)
        undone = {rb["rolled_back_commit"] for rb in rbs}
        for r in releases:
            full = git(repo, "rev-parse", r["sha"]).strip()
            if full in undone:
                r["rolled_back"] = True
        for rb in rbs:   # shown in "What's new"; the reason stays on the GitHub issue
            releases.append({"sha": rb["sha"][:7], "date": rb["date"], "from": "rollback",
                             "notes": "## ↩️ Rolled back\n\nThe previous update was undone while we "
                                      "fix a problem, so everything is back as it was before it. "
                                      "It will return once it's fixed."})
        releases.sort(key=lambda r: r["date"], reverse=True)
        data["releases"] = releases
        data["issues"] = issue_labels(r["notes"] for r in data["releases"])
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"{stage}: {len(data['releases'])} release(s), {len(data['recent'])} recent change(s)")


if __name__ == "__main__":
    main()
