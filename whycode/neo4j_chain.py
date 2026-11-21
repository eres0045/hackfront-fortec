"""WhyCode Neo4j store: the same graph, served from AuraDB over Bolt.

This module exists so the live app can answer from Neo4j — the partner
technology in the core flow — while SQLite stays the source of truth.
`Neo4jGraphStore` is duck-typed to `whycode.graph.GraphStore`: the same
methods, the same return shapes, the same ordering rules, so
`whycode.qa.ask()` and `whycode.alternatives` run on either store
without knowing which one they have.

How it stays identical:
- The mirror carries the FULL entity record (id, kind, title, body,
  url, created_at). Body is load-bearing: BM25 ranks over title+body,
  the refusal rules count body-only terms, DEP dates for the timeline
  live in the body, and the "why not" extractor reads DEP bodies.
  A title-only mirror would answer differently — that is why the
  mirror was changed to include body (see neo4j_mirror.py).
- Every relationship carries `seq`, its row index in SQLite's edges
  table. Neighbour order follows SQLite's own query planner exactly
  (out-neighbours by (dst, relation), in-neighbours by `seq`), so
  the evidence chain comes out in the same order.
- Token matching is done in Python with the same whole-word regex
  `GraphStore.find_by_tokens` uses — Cypher has no whole-word match,
  and reimplementing the matcher there would drift.
- The two raw-SQL reads in qa.py (`bm25_scores`) and alternatives.py
  (`find_alternative`) go through a tiny `.conn` shim that answers
  exactly those two queries from the loaded snapshot. Nothing else
  reads `store.conn`.

Serving shape: the graph is static for the finale, so the app loads
it ONCE per process into a read-only snapshot (`cached_store_from_env`)
and answers from that snapshot afterwards — the data is fetched from
Neo4j, not from SQLite, and a fresh load per question would cost
~5s a time (the bodies total ~1 MB over the wire). The snapshot is
keyed on the connection details, so different credentials reload
it; a failed load raises and the caller falls back to SQLite,
retrying Neo4j on the next request. `store_from_env` loads fresh
every call and exists for tests and one-off checks.

Failure mode: the constructor verifies connectivity and loads the
snapshot; ANY failure raises, and the caller (app.py) falls back to
SQLite silently. The store never returns partial data.
"""
import os
import re
import threading

from neo4j import GraphDatabase

# Keep the request fast: Aura answers in ms, but a hung network must
# never stall an evaluator's question past a few seconds.
CONNECT_TIMEOUT = 10


def _load_snapshot(uri, username, password, timeout=CONNECT_TIMEOUT):
    """(entities, out-adjacency, in-adjacency) fetched from Neo4j.

    One Bolt session, two queries, driver closed before returning —
    the snapshot is plain Python data after this. Raises on any
    failure (unreachable instance, bad credentials, timeout).
    """
    driver = GraphDatabase.driver(
        uri, auth=(username, password), connection_timeout=timeout)
    try:
        driver.verify_connectivity()
        with driver.session() as session:
            entity_rows = session.run(
                "MATCH (n:Entity) RETURN n.id AS id, n.kind AS kind, "
                "n.title AS title, n.body AS body, n.url AS url, "
                "n.created_at AS created_at"
            ).data()
            edge_rows = session.run(
                "MATCH (a:Entity)-[r]->(b:Entity) RETURN "
                "a.id AS src, b.id AS dst, type(r) AS relation, "
                "r.seq AS seq"
            ).data()
    finally:
        driver.close()
    entities = {}
    for row in entity_rows:
        entities[row["id"]] = {
            "id": row["id"],
            "kind": row["kind"],
            "title": row["title"],
            "body": row.get("body") or "",
            "url": row.get("url") or "",
            "created_at": row.get("created_at") or "",
        }
    # Neighbour order must match SQLite exactly, or the evidence
    # chain comes out in a different order. SQLite's own order is
    # an accident of its query planner, verified 21 Nov over all
    # 678 entities: out-neighbours come back in (dst, relation)
    # order (the edges PK index is (src, dst, relation), so a
    # WHERE on src reads it in index order), while in-neighbours
    # come back in edges-table rowid order (a WHERE on dst cannot
    # use that index prefix, so it is a full scan). `seq` is the
    # rowid order, captured by the mirror.
    # Relationship types are upper-cased in Neo4j by convention
    # (AUTHORED, SUPERSEDES, ...); the engine compares lowercase
    # ("authored", "supersedes"), so normalise here — a missed
    # lower() would silently break both the hop-2 authored
    # exclusion and the superseded banner.
    out = {}
    in_ = {}
    for row in edge_rows:
        edge = {"src": row["src"], "dst": row["dst"],
                "relation": row["relation"].lower(),
                "seq": row.get("seq") or 0}
        out.setdefault(edge["src"], []).append(edge)
        in_.setdefault(edge["dst"], []).append(edge)
    for edges in out.values():
        edges.sort(key=lambda e: (e["dst"], e["relation"]))
    for edges in in_.values():
        edges.sort(key=lambda e: e["seq"])
    return entities, out, in_


class _Rows:
    """fetchall() result for the .conn shim."""

    def __init__(self, rows):
        self._rows = rows

    def fetchall(self):
        return self._rows


class _Neo4jConnShim:
    """Minimal stand-in for sqlite3.Connection.

    Covers exactly the two raw-SQL reads the engine makes:
    - qa.bm25_scores: "SELECT id, title, body FROM entities"
    - alternatives.find_alternative: "SELECT * FROM entities WHERE kind = 'doc'"
    Anything else raises — a new raw-SQL read must be added here
    deliberately, not silently mis-answered.
    """

    def __init__(self, store):
        self._store = store

    def execute(self, sql, params=()):
        if "kind = 'doc'" in sql:
            rows = sorted(
                (dict(e) for e in self._store._entities.values()
                 if e["kind"] == "doc"),
                key=lambda e: e["id"],
            )
            return _Rows(rows)
        if "SELECT id, title, body FROM entities" in sql:
            rows = [
                {"id": e["id"], "title": e["title"], "body": e["body"]}
                for e in sorted(self._store._entities.values(),
                                key=lambda e: e["id"])
            ]
            return _Rows(rows)
        raise RuntimeError(
            f"unsupported SQL for Neo4j store: {sql!r}")


class Neo4jGraphStore:
    """GraphStore interface, backed by Neo4j AuraDB via the Bolt driver.

    Built from a snapshot — (entities, out-adjacency, in-adjacency)
    as loaded by `_load_snapshot` — so constructing a store is cheap
    and the snapshot can be shared read-only across requests (see
    `cached_store_from_env`). The snapshot is never mutated after
    load: every accessor returns fresh dicts, so sharing it between
    threads is safe. Constructing from connection details loads a
    fresh snapshot (used by tests and one-off checks).
    """

    def __init__(self, uri=None, username=None, password=None,
                 timeout=CONNECT_TIMEOUT, snapshot=None):
        if snapshot is None:
            if not (uri and username and password):
                raise ValueError(
                    "Neo4jGraphStore needs a snapshot or connection "
                    "details")
            snapshot = _load_snapshot(uri, username, password, timeout)
        self._entities, self._out, self._in = snapshot
        self.conn = _Neo4jConnShim(self)

    def close(self):
        # Snapshot stores hold no driver; kept so callers can close
        # unconditionally.
        return None

    def get_entity(self, id):
        ent = self._entities.get(id)
        return dict(ent) if ent else None

    def find_by_tokens(self, tokens):
        """Rank entities by how many question tokens appear as whole
        words in title/body — the same rule as GraphStore."""
        if not tokens:
            return []
        scored = []
        for ent in self._entities.values():
            words = set(re.findall(
                r"[a-z0-9_]+", (ent["title"] + " " + ent["body"]).lower()))
            matched = [t for t in tokens if t in words]
            if matched:
                scored.append((len(matched), dict(ent), matched))
        scored.sort(key=lambda s: (-s[0], s[1]["id"]))
        return scored

    def neighbors(self, entity_id, relation=None):
        out = []
        for edge in self._out.get(entity_id, []):
            if relation and edge["relation"] != relation:
                continue
            ent = self._entities.get(edge["dst"])
            if ent is None:
                continue
            rec = dict(ent)
            rec["relation"] = edge["relation"]
            out.append(rec)
        return out

    def neighbors_reverse(self, entity_id):
        out = []
        for edge in self._in.get(entity_id, []):
            ent = self._entities.get(edge["src"])
            if ent is None:
                continue
            rec = dict(ent)
            rec["relation"] = edge["relation"]
            out.append(rec)
        return out


def store_from_env():
    """Build a Neo4jGraphStore from NEO4J_URI/USERNAME/PASSWORD.

    Returns None when any variable is unset (Neo4j not configured —
    the caller falls back to SQLite). Raises on bad credentials or
    an unreachable instance, so the caller can fall back too.
    Loads a fresh snapshot on every call.
    """
    uri = os.environ.get("NEO4J_URI")
    username = os.environ.get("NEO4J_USERNAME")
    password = os.environ.get("NEO4J_PASSWORD")
    if not (uri and username and password):
        return None
    return Neo4jGraphStore(uri, username, password)


_SNAPSHOT = None
_SNAPSHOT_KEY = None
_SNAPSHOT_LOCK = threading.Lock()


def cached_store_from_env():
    """Neo4jGraphStore from the process-wide snapshot, or None.

    The snapshot loads once per process (keyed on the full
    connection triple) and is then shared read-only. A failed load
    raises — the caller falls back to SQLite and retries Neo4j on
    the next request. Different credentials reload the snapshot,
    so tests that swap env vars cannot see a stale instance.
    """
    global _SNAPSHOT, _SNAPSHOT_KEY
    uri = os.environ.get("NEO4J_URI")
    username = os.environ.get("NEO4J_USERNAME")
    password = os.environ.get("NEO4J_PASSWORD")
    if not (uri and username and password):
        return None
    key = (uri, username, password)
    if _SNAPSHOT is None or _SNAPSHOT_KEY != key:
        with _SNAPSHOT_LOCK:
            if _SNAPSHOT is None or _SNAPSHOT_KEY != key:
                _SNAPSHOT = _load_snapshot(uri, username, password)
                _SNAPSHOT_KEY = key
    return Neo4jGraphStore(snapshot=_SNAPSHOT)
