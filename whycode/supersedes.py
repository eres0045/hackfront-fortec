"""WhyCode supersedes edges: genuine override relationships from DEP text.

A supersedes edge points from an OLD decision to the NEW one that
replaced it, so QA can flag overridden decisions instead of quoting
them. Only edges the DEP text itself states — nothing is inferred:

- "This DEP supersedes DEP 4" / "supersedes both DEP 10 and DEP 12"
  (this DEP is the newer one; the named DEP is the old one).
- "has been superseded by DEP N" / ":Superseded-By: N" header
  (this DEP is the old one; N is the newer one).
- ":Replaces: N" header (this DEP replaces N; N is the old one).

Things that are NOT edges, checked against the live DB (21 Nov 2026):
- "subsumes the clarifications in DEP 44" (DEP 0020) — subsuming is
  not superseding; DEP 44's own status is Draft.
- "supersedes Django's previous, unwritten policy" (DEP 0007) — the
  old thing is a policy, not a DEP entity in the graph.
- "It's superseded by the DIRS setting" (DEP 0182), "should be
  replaced by defining a MAILERS alias" (DEP 0018) — settings/code,
  not DEPs.
- "DEPs can also be superseded by a different DEP" (DEP 0001) — the
  process description, not a statement about any DEP.
- "Status: Superseded" with no named DEP successor (DEP 0011 was
  superseded by a Working Group, not a DEP) — no target, no edge.

A DEP number shared by two entities in the graph (e.g. 0007 exists as
both a draft and a final DEP) is ambiguous: the edge is skipped, never
guessed. Skipped cases are reported, not silently dropped.
"""
import argparse
import json
import re

# "supersedes DEP 4", "supersedes both DEP 10 and DEP 12".
SUPERSEDES_RE = re.compile(
    r"supersede[s]?\s+(?:both\s+)?DEP\s+(\d+)"
    r"(?:\s+and\s+DEP\s+(\d+))?",
    re.IGNORECASE,
)
# "has been superseded by DEP 11" / "superseded by the DEP 11".
SUPERSEDED_BY_RE = re.compile(
    r"superseded\s+by\s+(?:the\s+)?DEP\s+(\d+)", re.IGNORECASE)
# RST header fields, one per line.
SUPERSEDED_BY_HEADER_RE = re.compile(
    r"^:Superseded-By:\s*(\d+)", re.IGNORECASE | re.MULTILINE)
REPLACES_HEADER_RE = re.compile(
    r"^:Replaces:\s*(\d+)", re.IGNORECASE | re.MULTILINE)

_ID_NUM_RE = re.compile(r"^dep:(\d+)-")


def _number_to_ids(store):
    """DEP number (int) -> sorted list of doc entity ids with that number.

    Numbers come from the id slug (dep:0010-...), not the title: the
    repo reuses numbers across statuses, so one number can map to two
    entities and the target is then ambiguous.
    """
    mapping = {}
    rows = store.conn.execute(
        "SELECT id FROM entities WHERE kind='doc'").fetchall()
    for (eid,) in rows:
        m = _ID_NUM_RE.match(eid)
        if not m:
            continue
        mapping.setdefault(int(m.group(1)), []).append(eid)
    return {n: sorted(ids) for n, ids in mapping.items()}


def _resolve(number_to_ids, number):
    """The single doc entity for a DEP number, or None if missing or
    ambiguous (two entities share the number)."""
    ids = number_to_ids.get(number)
    if not ids or len(ids) != 1:
        return None
    return ids[0]


def extract_supersedes_edges(store):
    """Scan doc bodies for stated supersedes relationships; add edges.

    Returns {"added": [(old_id, new_id), ...], "skipped": [reason, ...]}.
    Idempotent: edges are INSERT OR IGNORE, so re-running is safe.
    """
    number_to_ids = _number_to_ids(store)
    added, skipped = [], []
    rows = store.conn.execute(
        "SELECT id, body FROM entities WHERE kind='doc'").fetchall()
    for eid, body in rows:
        body = body or ""
        # (old_id, new_id) pairs claimed by this DEP's own text.
        claims = []
        for m in SUPERSEDES_RE.finditer(body):
            for num in (m.group(1), m.group(2)):
                if num:
                    claims.append((int(num), eid))  # named is old
        for m in SUPERSEDED_BY_RE.finditer(body):
            claims.append((eid, int(m.group(1))))  # named is new
        for m in SUPERSEDED_BY_HEADER_RE.finditer(body):
            claims.append((eid, int(m.group(1))))
        for m in REPLACES_HEADER_RE.finditer(body):
            claims.append((int(m.group(1)), eid))
        for old, new in claims:
            old_id = old if isinstance(old, str) else _resolve(
                number_to_ids, old)
            new_id = new if isinstance(new, str) else _resolve(
                number_to_ids, new)
            if old_id is None or new_id is None:
                missing = old if old_id is None else new
                skipped.append(
                    f"{eid}: DEP {missing} has no unique doc entity")
                continue
            if old_id == new_id:
                skipped.append(f"{eid}: self-supersedes, ignored")
                continue
            store.add_edge(old_id, new_id, "supersedes")
            added.append((old_id, new_id))
    # De-duplicate: the same claim can match twice (prose + header).
    added = sorted(set(added))
    return {"added": added, "skipped": sorted(set(skipped))}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="data/whycode.db")
    args = ap.parse_args()
    from whycode.graph import GraphStore
    store = GraphStore(args.db)
    report = extract_supersedes_edges(store)
    total = store.conn.execute(
        "SELECT COUNT(*) FROM edges WHERE relation='supersedes'"
    ).fetchone()[0]
    print(json.dumps({"added": [list(a) for a in report["added"]],
                      "skipped": report["skipped"],
                      "supersedes_edges_total": total}))


if __name__ == "__main__":
    main()
