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


def same_workflows(repo, sha):
    """True if this commit's .github/workflows folder matches main's current one."""
    def tree(rev):
        r = subprocess.run(["git", "-C", repo, "rev-parse", f"{rev}:.github/workflows"],
                           capture_output=True, text=True)
        return r.stdout.strip() if r.returncode == 0 else None
    return tree(sha) == tree("HEAD")


def existing_releases(slug):
    """Tag names that already have a GitHub release (empty if gh isn't available)."""
    res = subprocess.run(["gh", "api", f"repos/{slug}/releases", "--paginate",
                          "--jq", ".[].tag_name"], capture_output=True, text=True)
    return set(res.stdout.split()) if res.returncode == 0 else set()


def main():
    repo, slug = sys.argv[1], sys.argv[2]
    dry = "--dry-run" in sys.argv
    tz = ZoneInfo(os.environ.get("RELEASE_TZ") or "UTC")
    owner, name = slug.split("/", 1)
    site = f"https://{owner.lower()}.github.io/{name}/"

    have_release = set() if dry else existing_releases(slug)
    taken = release_tags(repo) | have_release
    todo, skipped = [], []
    for r in reversed(promotions(repo)):          # oldest first
        full = git(repo, "rev-parse", r["sha"]).strip()
        tag = tag_for(full, repo)                 # tag already on this commit?
        if tag and tag in have_release:
            continue
        new_tag = tag is None
        if new_tag and not same_workflows(repo, full):
            # GitHub won't let the deploy's token create a tag on an older
            # version whose workflow files differ from today's. Someone with
            # full access can push the tag; this script then adds the release.
            skipped.append(r["sha"])
            continue
        if new_tag:
            day = datetime.fromisoformat(r["date"]).astimezone(tz).strftime("%Y.%m.%d")
            tag = next_tag(day, taken)
            taken.add(tag)
        todo.append((tag, full, r, new_tag))

    if skipped:
        print(f"Releases: skipped {len(skipped)} older version(s) without a tag "
              f"({', '.join(skipped)}): their workflow files differ from today's, so "
              "the deploy can't tag them. Push a tag for one to have its release added.")
    if not todo:
        print("Releases: nothing new to create.")
        return
    failed = []
    for tag, sha, r, new_tag in todo:
        body = (r["notes"].strip() + f"\n\n---\nLive at {site}\n")
        title = f"{tag} (Production)"
        print(f"{'Would create' if dry else 'Creating'} {tag} -> {sha[:7]} ({r['date']})"
              + ("" if new_tag else " [tag already exists]"))
        if dry:
            continue
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write(body)
        cmd = ["gh", "release", "create", tag, "--repo", slug, "--title", title,
               "--notes-file", f.name]
        if new_tag:
            cmd += ["--target", sha]
        else:
            cmd += ["--verify-tag"]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            msg = (res.stderr or res.stdout).strip()
            print(f"::warning::Couldn't create release {tag} for {sha[:7]}: {msg}")
            failed.append(tag)
    if failed:
        print(f"::warning::{len(failed)} release(s) not created: {', '.join(failed)}. "
              "If GitHub said 403, check the app's deploy.yml has 'contents: write'. "
              "(see the playbook's stages-and-releases guide).")


if __name__ == "__main__":
    main()
