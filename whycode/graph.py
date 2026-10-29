"""WhyCode graph store: entities and edges in SQLite, stdlib only.

Entity kinds: commit, pr, issue, file, function, person, incident, doc.
Edge relations: authored, fixes, references, supersedes, mentions, touches,
decides. A supersedes edge points from an OLD decision to the NEW one that
replaced it, so QA can flag overridden decisions instead of quoting them.
"""
import sqlite3


class GraphStore:
    def __init__(self, path=":memory:"):
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS entities (
                id TEXT PRIMARY KEY,
                kind TEXT NOT NULL,
                title TEXT NOT NULL,
                body TEXT NOT NULL DEFAULT '',
                url TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT ''
            );
            CREATE TABLE IF NOT EXISTS edges (
                src TEXT NOT NULL,
                dst TEXT NOT NULL,
                relation TEXT NOT NULL,
                PRIMARY KEY (src, dst, relation)
            );
            """
        )

    def add_entity(self, id, kind, title, body="", url="", created_at=""):
        self.conn.execute(
            "INSERT OR REPLACE INTO entities VALUES (?,?,?,?,?,?)",
            (id, kind, title, body, url, created_at),
        )
        self.conn.commit()

    def add_edge(self, src, dst, relation):
        self.conn.execute(
            "INSERT OR IGNORE INTO edges VALUES (?,?,?)", (src, dst, relation)
        )
        self.conn.commit()

    def get_entity(self, id):
        row = self.conn.execute(
            "SELECT * FROM entities WHERE id = ?", (id,)
        ).fetchone()
        return dict(row) if row else None

    def neighbors_reverse(self, entity_id):
        """Entities pointing at this one (e.g. commits fixing a ticket)."""
        q = ("SELECT e.*, g.relation FROM edges g "
             "JOIN entities e ON e.id = g.src WHERE g.dst = ?")
        return [dict(r) for r in self.conn.execute(q, (entity_id,)).fetchall()]

    def find_by_tokens(self, tokens):
        """Rank entities by how many question tokens appear as whole words
        in title/body. Whole-word matching only: substring hits (e.g.
        "use" inside "users") are false evidence and must not count."""
        import re
        if not tokens:
            return []
        rows = self.conn.execute("SELECT * FROM entities").fetchall()
        scored = []
        for row in rows:
            words = set(re.findall(r"[a-z0-9_]+",
                                   (row["title"] + " " + row["body"]).lower()))
            matched = [t for t in tokens if t in words]
            if matched:
                scored.append((len(matched), dict(row), matched))
        scored.sort(key=lambda s: (-s[0], s[1]["id"]))
        return scored

    def neighbors(self, entity_id, relation=None):
        q = "SELECT e.*, g.relation FROM edges g JOIN entities e ON e.id = g.dst WHERE g.src = ?"
        args = [entity_id]
        if relation:
            q += " AND g.relation = ?"
            args.append(relation)
        return [dict(r) for r in self.conn.execute(q, args).fetchall()]
