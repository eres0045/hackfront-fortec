"""WhyCode Trac ingestion: Django tracks decisions in Trac tickets
(code.djangoproject.com), not GitHub Issues, so commit messages like
"Fixed #37089" point at Trac, not at GitHub issue numbers. This module
fetches those ticket pages (plain HTML, no auth needed) and turns them
into graph entities, so commit -> ticket edges carry the actual decision
rationale instead of dangling numbers.
"""
import argparse
import html as htmlmod
import json
import re
import sqlite3
import urllib.request

from whycode.graph import GraphStore
from whycode.ingest import REF_RE, link_refs

UA = "WhyCode-prototype/1.0 (hackFront demo research)"


def strip_tags(text):
    text = re.sub(r"<[^>]+>", " ", text)
    text = htmlmod.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def parse_ticket_html(page_html):
    """Extract title, description and first comments from a Trac page."""
    m = re.search(r"<title>\s*#\d+\s*\((.*?)\)\s*[–-]\s*Django\s*</title>",
                  page_html, re.S)
    title = strip_tags(m.group(1)) if m else ""
    body_parts = []
    dm = re.search(r'<div class="description">.*?<div class="searchable">'
                   r"(.*?)</div>", page_html, re.S)
    if dm:
        body_parts.append(strip_tags(dm.group(1))[:2000])
    comments = re.findall(r'<div class="comment searchable">(.*?)</div>',
                          page_html, re.S)
    for c in comments[:3]:
        t = strip_tags(c)
        if t:
            body_parts.append("Comment: " + t[:500])
    return {"title": title, "body": "\n\n".join(body_parts)}


def fetch_ticket(number):
    req = urllib.request.Request(
        f"https://code.djangoproject.com/ticket/{number}",
        headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.read().decode("utf-8", "replace")
    except Exception as e:
        print(f"ticket {number}: fetch failed ({type(e).__name__})")
        return None


def candidate_numbers(db_path, limit):
    """Trac ticket candidates, ranked by reliability of the source.

    Commit messages are the reliable source: Django's convention is that
    "Fixed #N" / "Refs #N" in a commit always names a Trac ticket. PR
    bodies are deliberately excluded: they mix GitHub PR numbers
    ("Supersedes #22077") that 404 on Trac and would crowd out real
    tickets. Full Trac URLs in any body are definite tickets too.
    """
    conn = sqlite3.connect(db_path)
    commit_counts = {}
    for (body,) in conn.execute(
            "SELECT body FROM entities WHERE kind='commit'"):
        for m in REF_RE.finditer(body or ""):
            commit_counts[m.group(1)] = commit_counts.get(m.group(1), 0) + 1
    url_numbers = []
    for (body,) in conn.execute("SELECT body FROM entities"):
        for m in re.finditer(r"code\.djangoproject\.com/ticket/(\d+)",
                             body or ""):
            if m.group(1) not in url_numbers:
                url_numbers.append(m.group(1))
    ranked = sorted(commit_counts, key=lambda n: -commit_counts[n])
    out = []
    for n in ranked + url_numbers:
        if n not in out:
            out.append(n)
    return out[:limit]


def ranked_ticket_numbers(db_path, limit):
    """Backwards-compatible alias: commit-sourced candidates only."""
    return candidate_numbers(db_path, limit)


def ingest_tickets(store, numbers):
    """Fetch tickets, store them as issue entities, relink commits/PRs."""
    done = 0
    number_to_id = {}
    for n in numbers:
        page = fetch_ticket(n)
        if not page:
            continue
        parsed = parse_ticket_html(page)
        if not parsed["title"]:
            continue
        eid = f"issue:{n}"
        number_to_id[n] = eid
        store.add_entity(eid, "issue", parsed["title"], parsed["body"],
                         f"https://code.djangoproject.com/ticket/{n}")
        done += 1
    for row in store.conn.execute(
            "SELECT id, body FROM entities WHERE kind IN ('commit','pr')"):
        link_refs(store, row[0], row[1], number_to_id)
    return done


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="data/whycode.db")
    ap.add_argument("--limit", type=int, default=60)
    args = ap.parse_args()
    numbers = candidate_numbers(args.db, args.limit)
    store = GraphStore(args.db)
    done = ingest_tickets(store, numbers)
    edges = store.conn.execute("SELECT COUNT(*) FROM edges").fetchone()[0]
    print(json.dumps({"tickets_ingested": done, "candidates": len(numbers),
                      "total_edges": edges}))


if __name__ == "__main__":
    main()
