"""WhyCode ingestion: GitHub -> graph, via the gh CLI (authenticated as
eres0045, so the 5,000/hr rate limit applies, not the anonymous 60/hr).

Scope is deliberately bounded: recent commits (headers), recent issues,
recent PRs, plus full file detail for the most-connected commits only.
The graph model scales to full history; the demo slice keeps judge runs
fast and API-cheap.

Linking rules (all derived from the repo's own text, never invented):
- commit message / PR body mentioning #NNN -> references edge to the
  issue or PR numbered NNN, when that entity was ingested.
- PR body saying fixes/closes/resolves #NNN -> fixes edge instead.
- commit author login -> person entity + authored edge.
- commit file list -> file entity + touches edge.
"""
import argparse
import json
import re
import subprocess

from whycode.graph import GraphStore

REF_RE = re.compile(r"#(\d+)")
FIX_RE = re.compile(r"\b(?:fixes|fixed|closes|closed|resolves|resolved)\s+#(\d+)", re.IGNORECASE)


def run_gh(path):
    out = subprocess.run(["gh", "api", path], capture_output=True, text=True,
                         timeout=120)
    if out.returncode != 0:
        raise RuntimeError(f"gh api {path} failed: {out.stderr.strip()[:300]}")
    return json.loads(out.stdout)


def paged(path, limit, per_page=100):
    """Collect up to `limit` items from a paged list endpoint."""
    items, page = [], 1
    while len(items) < limit:
        sep = "&" if "?" in path else "?"
        batch = run_gh(f"{path}{sep}per_page={per_page}&page={page}")
        if not isinstance(batch, list) or not batch:
            break
        items.extend(batch)
        if len(batch) < per_page:
            break
        page += 1
    return items[:limit]


def add_person(store, login):
    if login:
        store.add_entity(f"person:{login}", "person", login)


def link_refs(store, src_id, text, number_to_id):
    """Create references/fixes edges for every #NNN in text."""
    text = text or ""
    fixed = set()
    for m in FIX_RE.finditer(text):
        dst = number_to_id.get(m.group(1))
        if dst and dst != src_id:
            store.add_edge(src_id, dst, "fixes")
            fixed.add(m.group(1))
    for m in REF_RE.finditer(text):
        if m.group(1) in fixed:
            continue
        dst = number_to_id.get(m.group(1))
        if dst and dst != src_id:
            store.add_edge(src_id, dst, "references")


def build_graph(store, repo, n_commits=200, n_issues=100, n_prs=100,
                detail_commits=30):
    counts = {"commits": 0, "issues": 0, "prs": 0, "files": 0, "edges": 0}
    issues = paged(f"repos/{repo}/issues?state=all&sort=created&direction=desc",
                   n_issues)
    prs = paged(f"repos/{repo}/pulls?state=all&sort=created&direction=desc",
                n_prs)
    number_to_id = {}
    for it in issues:
        if "pull_request" in it:
            continue
        eid = f"issue:{it['number']}"
        number_to_id[str(it["number"])] = eid
        store.add_entity(eid, "issue", it["title"], it.get("body") or "",
                         it["html_url"], it["created_at"])
        add_person(store, (it.get("user") or {}).get("login"))
        if it.get("user"):
            store.add_edge(eid, f"person:{it['user']['login']}", "authored")
        counts["issues"] += 1
    for pr in prs:
        eid = f"pr:{pr['number']}"
        number_to_id.setdefault(str(pr["number"]), eid)
        store.add_entity(eid, "pr", pr["title"], pr.get("body") or "",
                         pr["html_url"], pr["created_at"])
        add_person(store, (pr.get("user") or {}).get("login"))
        if pr.get("user"):
            store.add_edge(eid, f"person:{pr['user']['login']}", "authored")
        counts["prs"] += 1
    commits = paged(f"repos/{repo}/commits?sha=main&sort=created&direction=desc",
                    n_commits)
    commit_ids = []
    for c in commits:
        sha = c["sha"]
        eid = f"commit:{sha[:12]}"
        commit_ids.append((eid, sha))
        msg = c["commit"]["message"]
        title = msg.splitlines()[0] if msg else sha
        author = (c.get("author") or {}).get("login") or \
            c["commit"]["author"]["name"]
        store.add_entity(eid, "commit", title, msg,
                         c["html_url"], c["commit"]["author"]["date"])
        add_person(store, author)
        store.add_edge(eid, f"person:{author}", "authored")
        counts["commits"] += 1
    # Link everything by #NNN references (commits reference issues/PRs).
    for eid, _ in commit_ids:
        ent = store.get_entity(eid)
        link_refs(store, eid, ent["body"], number_to_id)
    for pr in prs:
        link_refs(store, f"pr:{pr['number']}", pr.get("body") or "",
                  number_to_id)
    # File detail for the most-connected commits: rank by edge count.
    conn = store.conn.execute(
        "SELECT src, COUNT(*) c FROM edges GROUP BY src ORDER BY c DESC")
    ranked = [r[0] for r in conn.fetchall()
              if r[0].startswith("commit:")][:detail_commits]
    sha_of = dict((eid, sha) for eid, sha in commit_ids)
    for eid in ranked:
        detail = run_gh(f"repos/{repo}/commits/{sha_of[eid]}")
        for f in detail.get("files", []):
            fid = f"file:{f['filename']}"
            store.add_entity(fid, "file", f["filename"])
            store.add_edge(eid, fid, "touches")
            counts["files"] += 1
    counts["edges"] = store.conn.execute(
        "SELECT COUNT(*) FROM edges").fetchone()[0]
    return counts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default="django/django")
    ap.add_argument("--commits", type=int, default=200)
    ap.add_argument("--issues", type=int, default=100)
    ap.add_argument("--prs", type=int, default=100)
    ap.add_argument("--detail-commits", type=int, default=30)
    ap.add_argument("--db", default="data/whycode.db")
    args = ap.parse_args()
    import os
    os.makedirs(os.path.dirname(args.db) or ".", exist_ok=True)
    store = GraphStore(args.db)
    counts = build_graph(store, args.repo, args.commits, args.issues,
                         args.prs, args.detail_commits)
    print(json.dumps({"repo": args.repo, "db": args.db, **counts}))


if __name__ == "__main__":
    main()
