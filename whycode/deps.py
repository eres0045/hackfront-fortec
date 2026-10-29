"""WhyCode DEP ingestion: Django Enhancement Proposals (django/deps)
-> doc entities in the graph.

Each DEP file becomes one doc entity (number, title, status, full text
tokens). 'mentions' edges link a DEP doc to file entities it names, ONLY
where that file entity already exists in the graph. Two conservative
matching rules, both derived from the DEP's own text, never invented:

- Literal full path: the file entity's repo-relative path (e.g.
  django/db/models/query.py) appears verbatim in the DEP text.
- Dotted module form: the file's dotted path (slashes -> dots, minus
  .py) appears as a whole dotted token in the DEP text. __init__.py
  files are excluded from dotted matching: their dotted form is a
  package prefix (e.g. django.db) that appears in prose without naming
  a file. Files without a slash in their title (e.g. AUTHORS) are
  excluded from literal matching for the same reason.

The DEP id is the filename slug (dep:0009-async), not just the number:
the repo reuses numbers across statuses (0007 exists as both a draft
and a final DEP), so number-only ids would collide.
"""
import argparse
import json
import os
import re

from whycode.graph import GraphStore

STATUS_DIRS = ["accepted", "draft", "final", "rejected", "superseded",
               "withdrawn"]


def parse_dep(path, status_dir):
    with open(path, encoding="utf-8", errors="replace") as f:
        text = f.read()
    m = (re.search(r"^:DEP:\s*(\d+)", text, re.M)
         or re.search(r"^DEP:\s*(\d+)", text, re.M))
    number = m.group(1) if m else None
    if not number:
        m2 = re.match(r"(\d+)-", os.path.basename(path))
        number = m2.group(1) if m2 else None
    title = None
    m = (re.search(r"^DEP\s+\d+[A-Za-z]*:\s*(.+)$", text, re.M)
         or re.search(r"^#\s+DEP\s+\d+[A-Za-z]*:\s*(.+)$", text, re.M))
    if m:
        title = m.group(1).strip()
    if not title:
        for line in text.splitlines():
            s = line.strip()
            if (s and not set(s) <= set("=-~^\"'#")
                    and not s.startswith(("..", ":"))):
                title = s
                break
    m = (re.search(r"^:Status:\s*(.+)$", text, re.M)
         or re.search(r"^Status:\s*(.+)$", text, re.M))
    status = m.group(1).strip() if m else status_dir.capitalize()
    return {"number": number, "title": title or os.path.basename(path),
            "status": status, "text": text}


def link_files(store, dep_id, text):
    """mentions edges to already-existing file entities only."""
    n = 0
    rows = store.conn.execute(
        "SELECT id, title FROM entities WHERE kind='file'").fetchall()
    for fid, title in rows:
        hit = False
        if title and "/" in title and title in text:
            hit = True
        elif (title and title.endswith(".py")
                and not title.endswith("__init__.py")):
            dotted = title[:-3].replace("/", ".")
            if re.search(r"(?<![A-Za-z0-9_.])" + re.escape(dotted)
                         + r"(?![A-Za-z0-9_])", text):
                hit = True
        if hit:
            store.add_edge(dep_id, fid, "mentions")
            n += 1
    return n


def ingest_deps(store, deps_dir):
    docs, mentions = 0, 0
    for status_dir in STATUS_DIRS:
        d = os.path.join(deps_dir, status_dir)
        if not os.path.isdir(d):
            continue
        for fname in sorted(os.listdir(d)):
            if fname in ("README.rst",) or fname.startswith("template"):
                continue
            if not (fname.endswith(".rst") or fname.endswith(".md")):
                continue
            slug = os.path.splitext(fname)[0]
            parsed = parse_dep(os.path.join(d, fname), status_dir)
            eid = f"dep:{slug}"
            title = (f"DEP {parsed['number']}: {parsed['title']}"
                     if parsed["number"] else parsed["title"])
            body = (f"Status: {parsed['status']}\n"
                    f"Directory: {status_dir}\n\n{parsed['text']}")
            url = (f"https://github.com/django/deps/blob/main/"
                   f"{status_dir}/{fname}")
            store.add_entity(eid, "doc", title, body, url)
            docs += 1
            mentions += link_files(store, eid, parsed["text"])
    return docs, mentions


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="data/whycode.db")
    ap.add_argument("--deps-dir", required=True)
    args = ap.parse_args()
    store = GraphStore(args.db)
    docs, mentions = ingest_deps(store, args.deps_dir)
    kinds = dict(store.conn.execute(
        "SELECT kind, COUNT(*) FROM entities GROUP BY kind").fetchall())
    edges = store.conn.execute("SELECT COUNT(*) FROM edges").fetchone()[0]
    print(json.dumps({"docs_ingested": docs, "mentions_edges": mentions,
                      "entities_by_kind": kinds, "total_edges": edges}))


if __name__ == "__main__":
    main()
