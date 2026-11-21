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
import threading
import time

from flask import Flask, render_template, request

from whycode.features import (
    blast_radius,
    decision_freshness,
    decision_health,
    evidence_grade,
    load_bearing,
    who_to_ask,
)
from whycode.graph import GraphStore
from whycode.neo4j_chain import cached_store_from_env
from whycode.qa import ask, decision_timeline

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.environ.get("WHYCODE_DB", os.path.join(BASE_DIR, "data", "whycode.db"))

app = Flask(__name__)

# Baseline security headers (ArgosX baseline findings 1-6). CSP keeps the
# inline confidence-bar width working via style-src 'unsafe-inline'; there
# are no external resources (no CDN, self-contained CSS, inline SVG).
SECURITY_HEADERS = {
    "X-Frame-Options": "DENY",
    "Strict-Transport-Security": "max-age=63072000; includeSubDomains",
    "Content-Security-Policy": "default-src 'self'; style-src 'self' 'unsafe-inline'",
    "X-Content-Type-Options": "nosniff",
    "Permissions-Policy": "geolocation=(), camera=(), microphone=()",
    "Referrer-Policy": "strict-origin-when-cross-origin",
}


@app.after_request
def add_security_headers(response):
    for key, value in SECURITY_HEADERS.items():
        response.headers[key] = value
    return response


CANONICAL_URL = "https://whycode-ui.onrender.com"

# Input validation (Build Plan "Reliability & access"): questions longer
# than this are refused with a friendly message instead of being run
# through the engine — a 10k-char paste must never become a 10k-token
# scan of the graph.
MAX_QUESTION_LENGTH = 500

# Rate limiting (Build Plan "Reliability & access"): in-memory per-IP
# limit for the question route only, 30 requests/minute/IP. The Flask
# dev server is single-process, so a dict is enough; a lock guards it
# because the server is threaded. Bypassed while TESTING so the suite
# stays fast — the limit itself is proven by tests that flip TESTING
# off (see tests/test_reliability.py).
RATE_LIMIT_REQUESTS = 30
RATE_LIMIT_WINDOW = 60  # seconds
RATE_LIMIT_MESSAGE = (
    "Slow down — too many questions in the last minute. "
    "Try again in a moment."
)
_rate_hits = {}
_rate_lock = threading.Lock()


def _client_ip():
    # Behind Render, X-Forwarded-For holds the real client first.
    if request.access_route:
        return request.access_route[0]
    return request.remote_addr or "unknown"


def _rate_limit_allowed(ip):
    now = time.monotonic()
    with _rate_lock:
        hits = [t for t in _rate_hits.get(ip, [])
                if now - t < RATE_LIMIT_WINDOW]
        if len(hits) >= RATE_LIMIT_REQUESTS:
            _rate_hits[ip] = hits
            return False
        hits.append(now)
        _rate_hits[ip] = hits
        return True


def reset_rate_limits():
    """Clear all recorded hits (tests only)."""
    with _rate_lock:
        _rate_hits.clear()


@app.before_request
def apply_rate_limit():
    if app.testing:
        return None
    if request.endpoint != "index":
        return None
    if not _rate_limit_allowed(_client_ip()):
        return (
            render_template(
                "index.html", question="", result=None,
                notice=RATE_LIMIT_MESSAGE, examples=EXAMPLE_QUESTIONS,
                entities=None, edges=None,
            ),
            429,
            {"Retry-After": str(RATE_LIMIT_WINDOW)},
        )
    return None


@app.route("/robots.txt")
def robots():
    return (
        "User-agent: *\nAllow: /\n"
        f"Sitemap: {CANONICAL_URL}/sitemap.xml\n",
        200,
        {"Content-Type": "text/plain"},
    )


@app.route("/sitemap.xml")
def sitemap():
    from urllib.parse import quote

    urls = [
        "",
        "decisions",
        "health",
        "?q=" + quote(EXAMPLE_QUESTIONS[0]),
        "?q=" + quote(EXAMPLE_QUESTIONS[1]),
    ]
    body = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for u in urls:
        body.append(f"  <url><loc>{CANONICAL_URL}/{u}</loc></url>")
    body.append("</urlset>")
    return ("\n".join(body) + "\n", 200, {"Content-Type": "application/xml"})

EXAMPLE_QUESTIONS = [
    "Why does ignore_warnings match substrings by default?",
    "Why does Django use microservices?",
    "Why didn't Django fork instead of adding async?",
]

KIND_COLORS = {
    "commit": "#15803d",
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
    height = max(340, 70 + rows * 108 + 30)
    cx, cy = 150, height // 2
    parts = [
        f'<svg viewBox="0 0 780 {height}" width="100%" role="group" '
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
    chain_source = None
    if request.method == "POST":
        question = (request.form.get("question") or "").strip()
        if not question:
            notice = "Type a question first — for example, try one of the two below."
    elif "q" in request.args:
        # A ?q= link with nothing (or only spaces) in it is a submitted
        # empty question, not an initial page load — say so, like POST.
        question = (request.args.get("q") or "").strip()
        if not question:
            notice = "Type a question first — for example, try one of the two below."
    if question and len(question) > MAX_QUESTION_LENGTH:
        # Too long: friendly message, question kept in the box so it can
        # be trimmed down. Never run through the engine.
        notice = (
            f"That question is too long ({len(question)} characters — "
            f"the limit is {MAX_QUESTION_LENGTH}). "
            "Shorten it and try again."
        )
    elif question:
        result, chain_source = _answer(question)
    entities, edges = db_stats()
    return render_template(
        "index.html",
        question=question,
        result=result,
        notice=notice,
        examples=EXAMPLE_QUESTIONS,
        entities=entities,
        edges=edges,
        chain_source=chain_source,
    )


def _answer_with_store(store, question):
    """ask() plus the superseded banner, timeline and graph SVG."""
    result = ask(store, question)
    if not result.get("refused"):
        # Only an OUTGOING supersedes edge means this decision was
        # replaced (see qa.py): the newer decision's chain holds the
        # same edge incoming, and the banner must not fire on it.
        result["superseded"] = [
            e for e in result["evidence"]
            if e["relation"] == "supersedes" and e["direction"] == "out"
        ]
        result["timeline"] = decision_timeline(
            store, result["match"], result["evidence"])
        # New features: blast radius, freshness, grades, who-to-ask,
        # and the query that fetched the chain. All read the same
        # store the answer came from, so they agree with it — and
        # none of them touches the refusal rules above.
        result["blast"] = blast_radius(
            store, result["match"], result["evidence"])
        result["freshness"] = decision_freshness(
            store, result["match"], result["evidence"])
        result["who"] = who_to_ask(result["blast"])
        result["query_text"] = store.chain_query(result["match"]["id"])
        for rec in result["evidence"]:
            rec["grade"] = evidence_grade(rec)
        if result["evidence"]:
            result["graph_svg"] = evidence_graph_svg(
                result["match"], result["evidence"])
    return result


def _store_for_request():
    """(store, source): Neo4j first, SQLite fallback — same as _answer.

    The Neo4j store shares the process-wide snapshot; closing it is
    a no-op. The SQLite store is fresh per request (sqlite3
    connections are not thread-safe).
    """
    try:
        neo4j_store = cached_store_from_env()
    except Exception:
        neo4j_store = None
    if neo4j_store is not None:
        return neo4j_store, "neo4j"
    return GraphStore(DB_PATH), "sqlite"


def _close_store(store):
    close = getattr(store, "close", None)
    if close:
        try:
            close()
        except Exception:
            pass


@app.route("/decisions")
def decisions():
    """Load-bearing decisions: the top 10 docs by PageRank.

    The onboarding reading list — the decisions a new hire must
    understand first. Computed from the live graph on every load.
    """
    store, source = _store_for_request()
    try:
        rows = load_bearing(store)
    finally:
        _close_store(store)
    entities, edges = db_stats()
    return render_template(
        "decisions.html", rows=rows, entities=entities, edges=edges,
        chain_source=source)


@app.route("/health")
def health():
    """Decision health: every dated decision, ranked by code churn
    since it was made. The maintainer's page — the second user
    segment's live journey (Build Plan Challenge 05)."""
    store, source = _store_for_request()
    try:
        rows = decision_health(store)
    finally:
        _close_store(store)
    entities, edges = db_stats()
    return render_template(
        "health.html", rows=rows, entities=entities, edges=edges,
        chain_source=source)


def _answer(question):
    """(result, chain_source): Neo4j first, SQLite fallback.

    Neo4j is the partner technology in the core flow, so every
    question tries it first. ANY Neo4j failure — env vars unset,
    bad credentials, unreachable instance, a mid-query error —
    falls back to the SQLite store silently and still answers.
    The evaluator gets an answer either way, never a 500.
    """
    neo4j_store = None
    try:
        neo4j_store = cached_store_from_env()
    except Exception:
        neo4j_store = None
    if neo4j_store is not None:
        try:
            return _answer_with_store(neo4j_store, question), "neo4j"
        except Exception:
            pass
        finally:
            try:
                neo4j_store.close()
            except Exception:
                pass
    # Fresh store per request: sqlite3 connections are not thread-safe,
    # and the Flask dev server is threaded.
    return _answer_with_store(GraphStore(DB_PATH), question), "sqlite"


if __name__ == "__main__":
    # PORT is honoured so the same app runs on Render (which assigns $PORT).
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")))
