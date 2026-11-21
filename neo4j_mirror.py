#!/usr/bin/env python3
"""Mirror the WhyCode SQLite graph into Neo4j AuraDB (instance 'whycode').

Reads the SQLite DB (entities + edges) and loads it into Neo4j through
the Aura Query API (HTTPS, no driver needed). The password is read from
stdin (first line) and is never printed, logged or written to a file.
Auth travels in a temporary curl config file (0600, deleted after each
call), the same pattern as the Render API helper.

Usage:
  python3 neo4j_mirror.py --db data/whycode.db < password.txt

  (In practice the password is piped in, never stored in a file.)

Design (matches the UI's evidence chain):
  - One node per entity: (:Entity {id, kind, title, url, created_at}).
    `body` is deliberately NOT mirrored (PR bodies are long; the chain
    demo needs titles + links only).
  - One relationship per edge, type = relation upper-cased
    (AUTHORED, TOUCHES, FIXES, REFERENCES, MENTIONS). Relationship
    types cannot be parameterised in Cypher, so edges are loaded one
    statement per relation type.
  - SQLite stays the source of truth; this is a mirror for the
    Neo4j-served evidence chain in the core flow.
"""
import argparse
import base64
import json
import os
import sqlite3
import subprocess
import sys
import tempfile

URI = "https://9877c58b.databases.neo4j.io/db/9877c58b/query/v2"
USERNAME = "9877c58b"


def run_cypher(password, statement, parameters=None):
    """Run one Cypher statement via the Aura Query API. Returns the
    parsed JSON response. Raises RuntimeError on HTTP/API errors."""
    payload = {"statement": statement, "parameters": parameters or {}}
    auth = base64.b64encode(f"{USERNAME}:{password}".encode()).decode()
    body_file = cfg_file = None
    try:
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".json") as h:
            json.dump(payload, h)
            body_file = h.name
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".cfg") as h:
            h.write(f'header = "Authorization: Basic {auth}"\n')
            h.write('header = "Content-Type: application/json"\n')
            h.write('header = "Accept: application/json"\n')
            cfg_file = h.name
        os.chmod(cfg_file, 0o600)
        proc = subprocess.run(
            ["curl", "-s", "-K", cfg_file, "-X", "POST",
             "--data", "@" + body_file, "-w", "\n%{http_code}", URI],
            capture_output=True, text=True, timeout=120,
        )
    finally:
        for p in (body_file, cfg_file):
            if p:
                try:
                    os.unlink(p)
                except OSError:
                    pass
    out = proc.stdout
    body_text, _, code_text = out.rpartition("\n")
    try:
        status = int(code_text.strip())
    except ValueError:
        status = 0
    try:
        body = json.loads(body_text) if body_text.strip() else {}
    except json.JSONDecodeError:
        body = {"raw": body_text}
    if status >= 400 or "errors" in body:
        raise RuntimeError(f"Query API HTTP {status}: {json.dumps(body)[:500]}")
    return body


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default="data/whycode.db")
    args = parser.parse_args()
    password = sys.stdin.readline().strip()
    if not password:
        print("neo4j_mirror: no password on stdin", file=sys.stderr)
        sys.exit(1)

    conn = sqlite3.connect(args.db)
    entities = conn.execute(
        "SELECT id, kind, title, url, created_at FROM entities"
    ).fetchall()
    edges = conn.execute("SELECT src, dst, relation FROM edges").fetchall()
    print(f"SQLite: {len(entities)} entities, {len(edges)} edges")

    # Unique id so MERGE is safe to re-run.
    try:
        run_cypher(
            password,
            "CREATE CONSTRAINT entity_id_unique IF NOT EXISTS "
            "FOR (n:Entity) REQUIRE n.id IS UNIQUE",
        )
        print("constraint: entity_id_unique ok")
    except RuntimeError as e:
        print(f"constraint: skipped ({e})")

    node_stmt = (
        "UNWIND $rows AS row "
        "MERGE (n:Entity {id: row.id}) "
        "SET n.kind = row.kind, n.title = row.title, "
        "n.url = row.url, n.created_at = row.created_at"
    )
    for i in range(0, len(entities), 200):
        batch = [
            {"id": e[0], "kind": e[1], "title": e[2], "url": e[3],
             "created_at": e[4]}
            for e in entities[i:i + 200]
        ]
        run_cypher(password, node_stmt, {"rows": batch})
        print(f"nodes: {min(i + 200, len(entities))}/{len(entities)}")

    by_rel = {}
    for src, dst, rel in edges:
        by_rel.setdefault(rel, []).append({"src": src, "dst": dst})
    for rel, rows in sorted(by_rel.items()):
        rtype = rel.upper()
        stmt = (
            "UNWIND $rows AS row "
            "MATCH (a:Entity {id: row.src}), (b:Entity {id: row.dst}) "
            f"MERGE (a)-[:{rtype}]->(b)"
        )
        run_cypher(password, stmt, {"rows": rows})
        print(f"edges: {rel} ({len(rows)}) ok")

    nodes = run_cypher(password, "MATCH (n:Entity) RETURN count(n) AS c")
    rels = run_cypher(password, "MATCH ()-[r]->() RETURN count(r) AS c")
    n_count = nodes["data"][0]["row"][0]
    r_count = rels["data"][0]["row"][0]
    print(f"Neo4j: {n_count} nodes, {r_count} relationships")
    if n_count != len(entities) or r_count != len(edges):
        print("MISMATCH with SQLite counts!", file=sys.stderr)
        sys.exit(1)
    print("mirror complete: counts match SQLite")


if __name__ == "__main__":
    main()
