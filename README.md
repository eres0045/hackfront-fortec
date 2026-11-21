# WhyCode — Git remembers what changed. WhyCode remembers why.

Ask "why is the code like this?" and get an answer quoted from the project's
own record — a cited evidence chain, a confidence score, and an honest
refusal when the evidence is not there. No invented answers, ever.

**Live:** https://whycode.embarko.app — paste a repo link and ask about your
own code, or ask about the Django demo. No login, no signup.

Team FORTEC (Ronit Shrimankar + Udita Singh), hackFront India Grand Finale,
IIIT Delhi, 21–22 Nov 2026. Problem T1.1 — "Why The Code Is Like This".

## What it is

Codebases forget why. A senior answers "why is this like this?" from memory;
an AI agent changes code blind. WhyCode ingests a repo's commits, PRs,
tickets and design docs into a knowledge graph and answers "why" questions
from that graph — every claim linked to the commit, PR, ticket or DEP it
came from.

The demo corpus is **django/django**: 678 entities / 644 edges (200 commits,
100 PRs, 100 Trac tickets, 161 files, 90 people, 27 DEPs). Try:

- "Why does Django need a steering council?" → 0.99, with a **superseded**
  banner (DEP 0019 supersedes DEP 0010 + 0012)
- "Why didn't Django fork instead of adding async?" → the rejected
  alternative, cited verbatim from DEP 0009
- "Why should Django move to microservices?" → refused, not invented

## Features (finale build)

- **Evidence chain + confidence** on every answer, with a hand-rolled inline
  SVG graph view of the chain.
- **Blast radius** on every answer: files, commits and issues/PRs a change
  touches, plus who to ask.
- **Show the query**: the real SQL / Cypher that produced the answer, under
  each answer in a `<details>` block.
- **Load-bearing decisions** (`/decisions`): top-10 decisions ranked by
  PageRank (25-line stdlib implementation, no NetworkX).
- **Freshness + decision health** (`/health`): "decided on <date>, the code
  it governs changed <N> times since" — facts only, never a verdict.
- **Evidence grades A–D** on chain records; **who-to-ask** (top-2 authors by
  commits on the blast radius).
- **"Why NOT"**: alternatives a DEP proposed and rejected, quoted from the
  DEP text — plus a dated **decision timeline** per answer.
- **Supersedes banner**: 3 real edges from DEP text (DEP 0019 supersedes
  DEP 0010 + 0012; DEP 0020 supersedes DEP 0004). "Still true?" was
  evaluated and cut honestly — no verdict in the data is groundable.
- **Honest refusal** under 4 rules (no tokens / term absent / confidence
  < 0.35 / empty chain). BM25 ranking (title weighted 2×) inside the
  maximal token-coverage tier.
- **Reports**: `/digest` (monthly digest) + Reports nav on every page.
- **Reliability**: input validation, friendly messages for empty / too-long
  questions, rate limiting (30 req/min/IP on the question route),
  keep-alive so the free tier never cold-starts for an evaluator.

## Bring your own repo

Paste any **public GitHub repo URL** on the home page — no login. WhyCode
clones its history (commits, files, authors; max 300 commits, 90s cap) into
a per-repo SQLite graph and you ask the same "why" questions about your own
code. The Django demo is untouched; switch back with "Back to the Django
demo". One SQLite DB per repo under `data/repos/<owner>__<repo>.db`
(gitignored, max 3 repos kept). Ingest is rate-limited (5/hour/IP).

Stated plainly, the limits: history-only in v1 — no PRs/issues, no file
contents, nothing from the repo is ever executed. Public repos only, SQLite
only (no Neo4j for BYO repos), no auto-sync on push yet.

## Neo4j — inside the core flow

Neo4j AuraDB Free instance "whycode" (678 nodes / 644 relationships,
mirrored from SQLite, all with body). Honest split: the **MCP server**
serves evidence chains from Neo4j (Cypher, verified 0.99); the **Embarko
web copy** serves the same graph from SQLite (`chain-source: sqlite`).
SQLite is the source of truth and the fallback if Neo4j is unreachable.

## MCP server + PR bot

- **MCP server** (FastMCP, streamable HTTP): https://whycode-mcp.onrender.com/mcp
  — 4 tools on the same graph and refusal rules: `why_code`,
  `blast_radius`, `who_knows`, `decision_health`. Runs as a separate Render
  service (`uvicorn whycode.mcp_server:app`, deps in `requirements-mcp.txt`).
- **GitHub PR bot**: `POST /github-webhook` (HMAC-verified) comments on a
  PR only when a cited decision governs the PR's files — with blast radius
  and who to ask. It never blocks a merge. Raw GitHub REST via `requests`;
  no PyGithub (LGPL).

## Hosting

- Web app: https://whycode.embarko.app (claimed, permanent, free plan).
  The Render URL https://whycode-ui.onrender.com 302-redirects there
  (`/github-webhook` exempt, so the PR bot still answers on Render).
- MCP server: https://whycode-mcp.onrender.com (Render, free tier).

## Security

ArgosX free re-scan **99/100** (baseline was 81/100; all 13 findings fixed
live). Official report PDF in `docs/argosx-scan-report/`. Security headers
(HSTS, CSP, X-Frame-Options, nosniff, Permissions-Policy,
Referrer-Policy), robots.txt + sitemap.xml, axe-core 0 violations.

## Architecture

```text
ingest.py → trac.py → deps.py → graph.py   (SQLite: entities + edges)
qa.py                                        (ask, refusal, BM25, chain)
app.py                                       (Flask web UI, read-only)
whycode/neo4j_chain.py                       (Neo4j mirror + serving)
whycode/byo.py                               (BYO ingest: dulwich or git CLI)
whycode/mcp_server.py  whycode/prbot.py      (MCP server, PR bot)
```

The UI reads the answer object from `qa.py`; Neo4j swaps how the chain is
fetched, not its shape. Zero dependencies before the finale build; the web
app now needs only Flask + neo4j + requests + dulwich.

## Run it locally

```text
git clone https://github.com/eres0045/hackfront-fortec.git
cd hackfront-fortec
pip install -r requirements.txt
python app.py          # http://localhost:5000 (PORT env honoured)
```

The bundled `data/whycode.db` holds the demo graph, so the demo runs with
no API calls and no credentials. To rebuild it from scratch:

```text
python -m whycode.ingest --repo django/django --db data/whycode.db
python -m whycode.trac --db data/whycode.db --limit 100
```

Or ask from the CLI:

```text
python -m whycode.cli --db data/whycode.db --question "Why ...?"
```

Environment: `WHYCODE_DB` (path to the SQLite DB), `PORT`,
`WHYCODE_REDIRECT_TO` (redirect target — set on Render only),
`NEO4J_URI` / `NEO4J_USERNAME` / `NEO4J_PASSWORD` (optional; falls back to
SQLite silently). MCP server: `pip install -r requirements-mcp.txt` then
`uvicorn whycode.mcp_server:app`.

## Tests

```text
~/workspace/.venvs/neo4j/bin/python -m pytest tests/ -q
```

**121 passed, 7 skipped.** The 7 skipped tests need live Neo4j env vars
(they run green with a live instance). Run the suite with the neo4j venv —
system python lacks the driver.

## Docs

- `docs/finale-build-plan-v2-ui/` — the 1-page Finale Build Plan
- `docs/finale-build-plan-detailed/` — the full detail behind it
- `docs/argosx-scan-report/` — ArgosX reports (official PDF + summary)
- `docs/finale-notes.md` — build log for the finale
- `docs/oss-gold-research.md` — open-source components used / evaluated

## License

MIT — see `LICENSE`. "Every codebase has amnesia. WhyCode is its memory."
