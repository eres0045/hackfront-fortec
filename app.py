"""WhyCode web UI — Flask front end for the whycode answer engine.

Read-only over the engine: every answer comes from whycode.qa.ask() on the
bundled SQLite graph. This file never writes to the DB and never modifies
the engine. The graph view is an inline SVG rendered server-side from the
returned evidence chain (no JS library, no CDN, works offline).

Run:
  python3 app.py            # http://127.0.0.1:5000
  WHYCODE_DB=/path/to.db python3 app.py
"""
import html
import os
import sqlite3

from flask import Flask, render_template, request

from whycode.graph import GraphStore
from whycode.qa import ask

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.environ.get("WHYCODE_DB", os.path.join(BASE_DIR, "data", "whycode.db"))

app = Flask(__name__)

EXAMPLE_QUESTIONS = [
    "Why does ignore_warnings match substrings by default?",
    "Why does Django use microservices?",
]

KIND_COLORS = {
    "commit": "#16a34a",
    "pr": "#2563eb",
    "issue": "#b45309",
    "file": "#6b7280",
    "person": "#7c3aed",
    "doc": "#0e7490",
}


def db_stats():
    """Entity/edge counts for the footer; '-' if the DB is unreadable."""
    try:
        conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
        entities = conn.execute("SELECT COUNT(*) FROM entities").fetchone()[0]
        edges = conn.execute("SELECT COUNT(*) FROM edges").fetchone()[0]
        conn.close()
        return entities, edges
    except Exception:
        return None, None


def _wrap(text, width=26):
    """Word-wrap a title to lines of at most `width` chars (max 2 lines)."""
    words = text.split()
    lines, cur = [], ""
    for w in words:
        if cur and len(cur) + 1 + len(w) > width:
            lines.append(cur)
            cur = w
        else:
            cur = (cur + " " + w).strip()
    if cur:
        lines.append(cur)
    if len(lines) > 2:
        lines = lines[:2]
        lines[-1] = lines[-1][: width - 1].rstrip() + "…"
    return lines or [""]


def evidence_graph_svg(match, evidence):
    """Star-layout SVG of the evidence chain, centred on the best match.

    Each node is one record from the returned chain; edges are labelled with
    the relation and point in the record's direction (out = best match
    points at the record, in = the record points at the best match). Hop
    depth is collapsed: this is a rendering of the chain, not a re-walk.
    Nodes link to their record URL when one exists.
    """
    nodes = []
    seen = set()
    for rec in evidence:
        key = (rec["kind"], rec["title"])
        if key in seen:
            continue
        seen.add(key)
        nodes.append(rec)
    rows = len(nodes)
    height = max(460, 70 + rows * 108 + 30)
    cx, cy = 150, height // 2
    parts = [
        f'<svg viewBox="0 0 780 {height}" width="100%" role="img" '
        f'aria-label="Evidence chain graph" xmlns="http://www.w3.org/2000/svg">',
        "<defs><marker id=\"arr\" viewBox=\"0 0 10 10\" refX=\"9\" refY=\"5\" "
        "markerWidth=\"7\" markerHeight=\"7\" orient=\"auto-start-reverse\">"
        "<path d=\"M 0 0 L 10 5 L 0 10 z\" fill=\"#94a3b8\"/></marker></defs>",
    ]
    # Centre node: the best match.
    match_color = KIND_COLORS.get(match["kind"], "#334155")
    parts.append(
        f'<g><rect x="{cx - 95}" y="{cy - 34}" width="190" height="68" rx="8" '
        f'fill="#f0fdf4" stroke="{match_color}" stroke-width="2"/>'
        f'<text x="{cx}" y="{cy - 14}" text-anchor="middle" font-size="10" '
        f'fill="{match_color}" font-weight="bold">BEST MATCH · '
        f'{html.escape(match["kind"].upper())}</text>'
    )
    for i, line in enumerate(_wrap(match["title"], 26)):
        parts.append(
            f'<text x="{cx}" y="{cy + 4 + i * 14}" text-anchor="middle" '
            f'font-size="11" fill="#1a1a1a">{html.escape(line)}</text>')
    parts.append("</g>")
    # Evidence nodes in a single column on the right: one row per record, so
    # edge labels never stack on each other.
    for i, rec in enumerate(nodes):
        nx = 545
        ny = 70 + i * 108
        color = KIND_COLORS.get(rec["kind"], "#334155")
        # Edge: centre -> node (direction "out") or node -> centre ("in").
        # Endpoints sit just outside the node boxes so arrowheads stay visible.
        x1, y1 = (cx + 95, cy) if rec["direction"] == "out" else (nx - 97, ny + 6)
        x2, y2 = (nx - 97, ny + 6) if rec["direction"] == "out" else (cx + 95, cy)
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2 - 6
        parts.append(
            f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#94a3b8" '
            f'stroke-width="1.5" marker-end="url(#arr)"/>'
            f'<text x="{mx}" y="{my}" text-anchor="middle" font-size="10" '
            f'fill="#475569" font-style="italic" '
            f'style="paint-order: stroke; stroke: #ffffff; stroke-width: 4px;">'
            f'{html.escape(rec["relation"])}</text>')
        node = (
            f'<rect x="{nx - 95}" y="{ny - 30}" width="190" height="72" rx="8" '
            f'fill="#ffffff" stroke="{color}" stroke-width="1.5"/>'
            f'<text x="{nx}" y="{ny - 12}" text-anchor="middle" font-size="10" '
            f'fill="{color}" font-weight="bold">'
            f'{html.escape(rec["kind"].upper())}</text>'
        )
        for j, line in enumerate(_wrap(rec["title"], 26)):
            node += (
                f'<text x="{nx}" y="{ny + 6 + j * 14}" text-anchor="middle" '
                f'font-size="11" fill="#1a1a1a">{html.escape(line)}</text>')
        title = html.escape(f'{rec["title"]} ({rec["kind"]}, {rec["relation"]})')
        if rec.get("url"):
            parts.append(
                f'<a href="{html.escape(rec["url"], quote=True)}" target="_blank" '
                f'rel="noopener"><title>{title}</title>{node}</a>')
        else:
            parts.append(f"<g><title>{title}</title>{node}</g>")
    parts.append("</svg>")
    return "".join(parts)


@app.route("/", methods=["GET", "POST"])
def index():
    question = ""
    result = None
    notice = None
    if request.method == "POST":
        question = (request.form.get("question") or "").strip()
        if not question:
            notice = "Type a question first — for example, try one of the two below."
    elif request.args.get("q"):
        question = request.args.get("q").strip()
    if question and request.method in ("GET", "POST"):
        # Fresh store per request: sqlite3 connections are not thread-safe,
        # and the Flask dev server is threaded.
        result = ask(GraphStore(DB_PATH), question)
        if not result.get("refused"):
            result["superseded"] = [
                e for e in result["evidence"] if e["relation"] == "supersedes"
            ]
            result["graph_svg"] = evidence_graph_svg(
                result["match"], result["evidence"])
    entities, edges = db_stats()
    return render_template(
        "index.html",
        question=question,
        result=result,
        notice=notice,
        examples=EXAMPLE_QUESTIONS,
        entities=entities,
        edges=edges,
    )


if __name__ == "__main__":
    # PORT is honoured so the same app runs on Render (which assigns $PORT).
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")))
