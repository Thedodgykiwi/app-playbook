#!/usr/bin/env python3
"""Create a GitHub release for every Production release that doesn't have one.

Usage: make_releases.py <repo_dir> <owner/repo> [--dry-run]

<repo_dir> must be a full clone (with tags) checked out at `main`.

Every promotion into `main` (a "Promote staging → main" merge commit, or a
pull request merged into main) is one Production release. Each gets a tag
named after its date, and a release whose notes are the same plain-English
release notes the app shows under "What's new":

    v2026.11.13      1st Production release that day
    v2026.11.13.2    2nd the same day, then .3, .4 ... (by position in the day,
                     so names never depend on which other releases exist)

Issues mentioned in the release's changes ("Issue #12", "Fixes #12") are
closed with a comment naming the release (the notes themselves stay plain
English, with no issue numbers),
so they close when the fix is live in Production, whatever the repo's
default branch is.

It looks at the whole history every time, so a release that was missed (or
releases made before this existed) is filled in on the next run. Releases
that already exist are left alone. Run oldest first so GitHub marks the
newest as "Latest".

Dates use the timezone in RELEASE_TZ (an IANA name such as
"Pacific/Auckland"); default UTC.
"""
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from release_notes import git, promotions  # noqa: E402  (same folder)


def tag_for(sha, repo):
    """The release tag already on this commit, if any."""
    out = git(repo, "tag", "--points-at", sha, "--list", "v[0-9][0-9][0-9][0-9].*")
    return out.split()[0] if out.split() else None


def same_workflows(repo, sha):
    """True if this commit's .github/workflows folder matches main's current one."""
    def tree(rev):
        r = subprocess.run(["git", "-C", repo, "rev-parse", f"{rev}:.github/workflows"],
                           capture_output=True, text=True)
        return r.stdout.strip() if r.returncode == 0 else None
    return tree(sha) == tree("HEAD")


ISSUE_REF = re.compile(r"\b(?:issues?|fix(?:es|ed)?|close[sd]?|resolve[sd]?)\s*:?\s*#(\d+)", re.I)


def issues_in(repo, sha):
    """Issue numbers mentioned in the changes this promotion brought into main
    ("Issue #12", "Fixes #12", "Closes #3, #4" ...)."""
    log = git(repo, "log", "--format=%B", f"{sha}^1..{sha}")
    nums = set()
    for m in ISSUE_REF.finditer(log):
        nums.add(int(m.group(1)))
    # "Issue #3, #4" style lists: pick up the extra numbers after a match
    for line in log.splitlines():
        if ISSUE_REF.search(line):
            nums.update(int(n) for n in re.findall(r"#(\d+)", line))
    return sorted(nums)


def close_issues(slug, nums, tag, site):
    """Close each still-open issue with a comment naming the release."""
    for n in nums:
        view = subprocess.run(["gh", "issue", "view", str(n), "--repo", slug, "--json", "state"],
                              capture_output=True, text=True)
        if view.returncode != 0:
            continue                      # not an issue (e.g. a pull request number)
        if json.loads(view.stdout).get("state") != "OPEN":
            continue
        rel = f"https://github.com/{slug}/releases/tag/{tag}"
        body = (f"🚀 Released to **Production** in [{tag}]({rel}): live at {site}\n\n"
                "Closed automatically by the release.")
        res = subprocess.run(["gh", "issue", "close", str(n), "--repo", slug,
                              "--reason", "completed", "--comment", body],
                             capture_output=True, text=True)
        if res.returncode == 0:
            print(f"Issues: closed #{n} (released in {tag})")
        else:
            msg = (res.stderr or res.stdout).strip()
            print(f"::warning::Couldn't close issue #{n}: {msg} "
                  "(the app's deploy.yml needs 'issues: write').")


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

    # A release's name comes only from its position in the day, so it never
    # depends on which other releases happen to exist:
    #   1st Production release of a day -> v2026.11.13, 2nd -> v2026.11.13.2 ...
    per_day = {}
    plan = []                                     # (canonical tag, sha, release info)
    for r in reversed(promotions(repo)):          # oldest first
        full = git(repo, "rev-parse", r["sha"]).strip()
        day = datetime.fromisoformat(r["date"]).astimezone(tz).strftime("%Y.%m.%d")
        per_day[day] = per_day.get(day, 0) + 1
        n = per_day[day]
        plan.append((f"v{day}" if n == 1 else f"v{day}.{n}", full, r))

    have_release = set() if dry else existing_releases(slug)
    actions, skipped = [], []
    for tag, sha, r in plan:
        current = tag_for(sha, repo)              # our tag already on this commit?
        if current == tag and tag in have_release:
            continue                              # all good
        if current and current != tag and current in have_release:
            actions.append(("rename", current, tag, sha, r))
        elif current == tag:
            actions.append(("release", tag, tag, sha, r))   # tag exists, no release yet
        elif same_workflows(repo, sha):
            actions.append(("create", None, tag, sha, r))
        else:
            # GitHub won't let the deploy's token create a tag on an older
            # version whose workflow files differ from today's. Someone with
            # full access can push the tag; this script then adds the release.
            skipped.append(f"{r['sha']} ({tag})")

    if skipped:
        print(f"Releases: skipped {len(skipped)} older version(s) the deploy can't tag: "
              f"{', '.join(skipped)}. Push that tag to have its release added.")
    if not actions:
        print("Releases: nothing new to create.")
        return

    failed = []
    for kind, old, tag, sha, r in actions:
        label = {"create": f"Creating {tag}", "release": f"Adding release for existing tag {tag}",
                 "rename": f"Renaming {old} -> {tag}"}[kind]
        nums = issues_in(repo, sha) if kind != "rename" else []
        print(f"{'Would do: ' if dry else ''}{label} ({sha[:7]}, {r['date']})"
              + (f" closing issues {', '.join(f'#{n}' for n in nums)}" if nums else ""))
        if dry:
            continue
        if kind == "rename":
            cmds = [["gh", "release", "edit", old, "--repo", slug, "--tag", tag,
                     "--title", f"{tag} (Production)"],
                    ["gh", "api", "-X", "DELETE", f"repos/{slug}/git/refs/tags/{old}"]]
        else:
            # Notes stay exactly the plain-English release notes: issue
            # numbers go on the issues (closing comment), not in the notes.
            body = r["notes"].strip() + f"\n\n---\nLive at {site}\n"
            with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as f:
                f.write(body)
            cmd = ["gh", "release", "create", tag, "--repo", slug,
                   "--title", f"{tag} (Production)", "--notes-file", f.name]
            cmd += ["--target", sha] if kind == "create" else ["--verify-tag"]
            cmds = [cmd]
        ok = True
        for cmd in cmds:
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode != 0:
                msg = (res.stderr or res.stdout).strip()
                print(f"::warning::{label} failed: {msg}")
                failed.append(tag)
                ok = False
                break
        if ok and kind != "rename" and nums:
            close_issues(slug, nums, tag, site)
    if failed:
        print(f"::warning::{len(failed)} release step(s) failed: {', '.join(failed)}. "
              "If GitHub said 403, check the app's deploy.yml has 'contents: write' "
              "(see the playbook's stages-and-releases guide).")


if __name__ == "__main__":
    main()
