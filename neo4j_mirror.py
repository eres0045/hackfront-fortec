#!/usr/bin/env python3
"""Mirror the WhyCode SQLite graph into Neo4j AuraDB (Bolt driver).

Reads the SQLite DB (entities + edges) and loads it into Neo4j through
the Bolt driver (neo4j+s://, port 7687). The Aura HTTPS Query API is
UNREACHABLE from this VM (hangs on port 443, probed 2026-11-21), but
Bolt 7687 completes TCP + TLS fine — so the driver is the only working
transport from here.

The password is read from stdin (first line) and is never printed,
logged or written to a file. URI and username are CLI args because a
fresh instance gets a new ID/URI (the original whycode instance's
credentials were lost; Aura has no password reset).

Usage:
  ~/workspace/.venvs/neo4j/bin/python neo4j_mirror.py \
      --db data/whycode.db \
      --uri neo4j+s://<instance-id>.databases.neo4j.io \
      --username <instance-id> < password.txt

  (In practice the password is piped in via the exec tool's stdin,
  never stored in a file.)

Design (matches the UI's evidence chain):
  - One node per entity: (:Entity {id, kind, title, body, url, created_at}).
    `body` IS mirrored: ranking (BM25 over title+body), the refusal
    rules (a term that appears only in a body still counts), the
    decision timeline (DEP dates live in the body) and the "why not"
    extractor all read body — without it the Neo4j-served answers
    would differ from SQLite. Total body text is ~1 MB, max 68 KB
    per entity; AuraDB Free holds 1 GB, so this fits easily.
  - One relationship per edge, type = relation upper-cased
    (AUTHORED, TOUCHES, FIXES, REFERENCES, MENTIONS, SUPERSEDES).
    Relationship types cannot be parameterised in Cypher, so edges are
    loaded one statement per relation type. Each relationship also
    carries `seq`, its row index in SQLite's edges table, so a
    Neo4j-backed store can iterate neighbours in exactly the SQLite
    order and produce byte-identical evidence chains.
  - SQLite stays the source of truth; this is a mirror for the
    Neo4j-served evidence chain in the core flow.
"""
import argparse
import sqlite3
import sys

from neo4j import GraphDatabase


def run_cypher(driver, statement, parameters=None):
    """Run one Cypher statement via Bolt. Returns a list of dict rows.
    Raises on any driver/API error."""
    with driver.session() as session:
        result = session.run(statement, parameters or {})
        return [dict(r) for r in result]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default="data/whycode.db")
    parser.add_argument("--uri", required=True)
    parser.add_argument("--username", required=True)
    args = parser.parse_args()
    password = sys.stdin.readline().strip()
    if not password:
        print("neo4j_mirror: no password on stdin", file=sys.stderr)
        sys.exit(1)

    conn = sqlite3.connect(args.db)
    entities = conn.execute(
        "SELECT id, kind, title, url, created_at, body FROM entities"
    ).fetchall()
    edges = conn.execute("SELECT src, dst, relation FROM edges").fetchall()
    print(f"SQLite: {len(entities)} entities, {len(edges)} edges")

    driver = GraphDatabase.driver(args.uri, auth=(args.username, password))
    try:
        driver.verify_connectivity()
        print("Bolt: connected")

        # Unique id so MERGE is safe to re-run.
        try:
            run_cypher(
                driver,
                "CREATE CONSTRAINT entity_id_unique IF NOT EXISTS "
                "FOR (n:Entity) REQUIRE n.id IS UNIQUE",
            )
            print("constraint: entity_id_unique ok")
        except Exception as e:
            print(f"constraint: skipped ({e})")

        node_stmt = (
            "UNWIND $rows AS row "
            "MERGE (n:Entity {id: row.id}) "
            "SET n.kind = row.kind, n.title = row.title, "
            "n.body = row.body, n.url = row.url, n.created_at = row.created_at"
        )
        for i in range(0, len(entities), 200):
            batch = [
                {"id": e[0], "kind": e[1], "title": e[2], "url": e[3],
                 "created_at": e[4], "body": e[5]}
                for e in entities[i:i + 200]
            ]
            run_cypher(driver, node_stmt, {"rows": batch})
            print(f"nodes: {min(i + 200, len(entities))}/{len(entities)}")

        by_rel = {}
        for seq, (src, dst, rel) in enumerate(edges):
            by_rel.setdefault(rel, []).append(
                {"src": src, "dst": dst, "seq": seq})
        for rel, rows in sorted(by_rel.items()):
            rtype = rel.upper()
            stmt = (
                "UNWIND $rows AS row "
                "MATCH (a:Entity {id: row.src}), (b:Entity {id: row.dst}) "
                f"MERGE (a)-[r:{rtype}]->(b) SET r.seq = row.seq"
            )
            run_cypher(driver, stmt, {"rows": rows})
            print(f"edges: {rel} ({len(rows)}) ok")

        n_count = run_cypher(
            driver, "MATCH (n:Entity) RETURN count(n) AS c")[0]["c"]
        r_count = run_cypher(
            driver, "MATCH ()-[r]->() RETURN count(r) AS c")[0]["c"]
        n_body = run_cypher(
            driver,
            "MATCH (n:Entity) WHERE n.body IS NOT NULL "
            "RETURN count(n) AS c")[0]["c"]
        print(f"Neo4j: {n_count} nodes, {r_count} relationships, "
              f"{n_body} nodes with body")
        if n_count != len(entities) or r_count != len(edges):
            print("MISMATCH with SQLite counts!", file=sys.stderr)
            sys.exit(1)
        if n_body != len(entities):
            print("MISMATCH: not every node has a body!", file=sys.stderr)
            sys.exit(1)
        print("mirror complete: counts match SQLite")
    finally:
        driver.close()


if __name__ == "__main__":
    main()
