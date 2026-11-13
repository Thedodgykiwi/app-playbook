#!/usr/bin/env python3
"""Create a GitHub release for every Production release that doesn't have one.

Usage: make_releases.py <repo_dir> <owner/repo> [--dry-run]

<repo_dir> must be a full clone (with tags) checked out at `main`.

Every promotion into `main` (a "Promote staging → main" merge commit, or a
pull request merged into main) is one Production release. Each gets a tag
named after its date, and a release whose notes are the same plain-English
release notes the app shows under "What's new":

    v2026.11.13      first release that day
    v2026.11.13.2    second release the same day, then .3, .4 ...

It looks at the whole history every time, so a release that was missed (or
releases made before this existed) is filled in on the next run. Releases
that already exist are left alone. Run oldest first so GitHub marks the
newest as "Latest".

Dates use the timezone in RELEASE_TZ (an IANA name such as
"Pacific/Auckland"); default UTC.
"""
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from release_notes import git, promotions  # noqa: E402  (same folder)


def release_tags(repo):
    """Tags that look like ours: vYYYY.MM.DD or vYYYY.MM.DD.N."""
    out = git(repo, "tag", "--list", "v[0-9][0-9][0-9][0-9].[0-9][0-9].[0-9][0-9]*")
    return set(out.split())


def tag_for(sha, repo):
    """The release tag already on this commit, if any."""
    out = git(repo, "tag", "--points-at", sha, "--list", "v[0-9][0-9][0-9][0-9].*")
    return out.split()[0] if out.split() else None


def next_tag(day, taken):
    base = f"v{day}"
    if base not in taken:
        return base
    n = 2
    while f"{base}.{n}" in taken:
        n += 1
    return f"{base}.{n}"


def main():
    repo, slug = sys.argv[1], sys.argv[2]
    dry = "--dry-run" in sys.argv
    tz = ZoneInfo(os.environ.get("RELEASE_TZ") or "UTC")
    owner, name = slug.split("/", 1)
    site = f"https://{owner.lower()}.github.io/{name}/"

    taken = release_tags(repo)
    todo = []
    for r in reversed(promotions(repo)):          # oldest first
        full = git(repo, "rev-parse", r["sha"]).strip()
        if tag_for(full, repo):
            continue
        day = datetime.fromisoformat(r["date"]).astimezone(tz).strftime("%Y.%m.%d")
        tag = next_tag(day, taken)
        taken.add(tag)
        todo.append((tag, full, r))

    if not todo:
        print("Releases: all Production releases already have a GitHub release.")
        return
    for tag, sha, r in todo:
        body = (r["notes"].strip() + f"\n\n---\nLive at {site}\n")
        title = f"{tag} (Production)"
        print(f"{'Would create' if dry else 'Creating'} {tag} -> {sha[:7]} ({r['date']})")
        if dry:
            continue
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write(body)
        res = subprocess.run(["gh", "release", "create", tag, "--repo", slug,
                              "--target", sha, "--title", title, "--notes-file", f.name],
                             capture_output=True, text=True)
        if res.returncode != 0:
            msg = (res.stderr or res.stdout).strip()
            if "403" in msg or "Resource not accessible" in msg:
                print("::warning::Can't create GitHub releases: the app's deploy.yml needs "
                      "'contents: write' under permissions (see the playbook template).")
                return
            print(msg)
            sys.exit(1)


if __name__ == "__main__":
    main()
