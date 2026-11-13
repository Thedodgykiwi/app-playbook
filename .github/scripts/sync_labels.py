#!/usr/bin/env python3
"""Make sure an app repo has the shared issue labels.

Usage: sync_labels.py <labels.json> <owner/repo>

The labels live once, in the playbook's .github/labels.json. Each label is
created, or its colour/description updated to match. Other labels in the
repo (e.g. GitHub's defaults) are left alone. Needs `issues: write` in the
app's deploy.yml; without it this prints a note and does nothing.
"""
import json
import subprocess
import sys


def main():
    path, slug = sys.argv[1], sys.argv[2]
    labels = json.load(open(path, encoding="utf-8"))
    done = 0
    for l in labels:
        res = subprocess.run(["gh", "label", "create", l["name"], "--repo", slug, "--force",
                              "--color", l["color"], "--description", l["description"]],
                             capture_output=True, text=True)
        if res.returncode != 0:
            msg = (res.stderr or res.stdout).strip()
            if "403" in msg or "Resource not accessible" in msg:
                print("Labels: not updated (the app's deploy.yml needs 'issues: write').")
                return
            print(f"::warning::Label '{l['name']}' failed: {msg}")
            continue
        done += 1
    print(f"Labels: {done}/{len(labels)} shared labels in place.")


if __name__ == "__main__":
    main()
