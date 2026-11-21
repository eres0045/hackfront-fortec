"""WhyCode BYO (Bring-Your-Own-Repo) Ingestion:
Extracts git history from any local or cloned git repository into WhyCode GraphStore.

Extracts:
- commits (title, body, hash, date)
- authors (login/name) + 'authored' edges
- files touched + 'touches' edges
- #NNN issue/PR references + 'references' / 'fixes' edges
"""

import os
import re
import subprocess
import sys

# Ensure package root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Dict, Any
from whycode.graph import GraphStore
from whycode.ingest import FIX_RE, REF_RE
from whycode.security import scrub_text


def ingest_git_repo(repo_dir: str, store: GraphStore, max_commits: int = 300) -> Dict[str, int]:
    """Ingest git log directly from a local git repository without any API calls."""
    if not os.path.isdir(os.path.join(repo_dir, ".git")):
        raise ValueError(f"Not a valid git repository: {repo_dir}")

    # Format: hash%x1fauthor%x1fdate%x1fsubject%x1fbody%x1e
    cmd = [
        "git", "-C", repo_dir, "log",
        f"-n{max_commits}",
        "--name-only",
        "--format=%H%x1f%an%x1f%ad%x1f%s%x1f%b%x1e"
    ]
    out = subprocess.run(cmd, capture_output=True, text=True, errors="replace", check=True)
    raw_entries = out.stdout.split("\x1e")

    counts = {"commits": 0, "people": 0, "files": 0, "edges": 0}
    seen_people = set()
    seen_files = set()

    for entry in raw_entries:
        entry = entry.strip()
        if not entry:
            continue
        parts = entry.split("\x1f")
        if len(parts) < 5:
            continue

        commit_hash = parts[0].strip()
        author_raw = parts[1].strip()
        date = parts[2].strip()
        subject_raw = parts[3].strip()
        rest = parts[4].strip()

        # Proven Gitleaks/Presidio Pre-Ingest Sanitization
        subject, _ = scrub_text(subject_raw)
        author, _ = scrub_text(author_raw, redact_secrets=False, check_entropy=False)

        # The rest contains body followed by touched files
        body_and_files = rest.split("\n\n")
        body_raw = body_and_files[0].strip() if body_and_files else ""
        body, _ = scrub_text(body_raw)
        touched_files = []
        if len(body_and_files) > 1:
            # Lines at the end are file paths
            file_lines = body_and_files[-1].strip().splitlines()
            touched_files = [f.strip() for f in file_lines if f.strip() and not " " in f.strip() and ("." in f or "/" in f)]

        cid = f"commit:{commit_hash[:12]}"
        full_text = f"{subject}\n\n{body}" if body else subject

        # Add commit entity
        store.add_entity(cid, "commit", subject, full_text, url="", created_at=date)
        counts["commits"] += 1

        # Author person entity + edge
        if author:
            pid = f"person:{author}"
            if pid not in seen_people:
                store.add_entity(pid, "person", author)
                seen_people.add(pid)
                counts["people"] += 1
            store.add_edge(cid, pid, "authored")
            counts["edges"] += 1

        # File touches
        for fpath in touched_files[:15]:  # limit to top 15 files per commit to avoid bloating
            fid = f"file:{fpath}"
            if fid not in seen_files:
                store.add_entity(fid, "file", fpath)
                seen_files.add(fid)
                counts["files"] += 1
            store.add_edge(cid, fid, "touches")
            counts["edges"] += 1

        # Issue/PR references
        for m in FIX_RE.finditer(full_text):
            num = m.group(1)
            iid = f"issue:{num}"
            store.add_entity(iid, "issue", f"Issue #{num}")
            store.add_edge(cid, iid, "fixes")
            counts["edges"] += 1

        for m in REF_RE.finditer(full_text):
            num = m.group(1)
            iid = f"issue:{num}"
            store.add_entity(iid, "issue", f"Issue/PR #{num}")
            store.add_edge(cid, iid, "references")
            counts["edges"] += 1

    return counts


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--db", default="data/requests.db")
    ap.add_argument("--limit", type=int, default=300)
    args = ap.parse_args()

    s = GraphStore(args.db)
    res = ingest_git_repo(args.repo, s, args.limit)
    print(f"Ingested from {args.repo} into {args.db}: {res}")
