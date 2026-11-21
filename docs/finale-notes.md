# WhyCode — Finale Build Notes

Written Sat 21 Nov 2026, ~11:00 IST, from a full read of the code + live verification.
Team tonight: Ronit (lead) + Udita. Anshul is NOT attending.
Build clock: Sat 14:00 IST → Sun 12:00 code freeze, IIIT Delhi, overnight at the venue.
Rule for the night: only a LIVE working product counts. No recording, no mockup.
Everything below was verified by running it, not by reading claims.

## 1. What the system does (5 lines)

1. Ingests a public repo (django/django) — commits, PRs, issues, Trac tickets, DEPs — into a graph.
2. A question like "Why does X work like this?" is tokenised and matched against graph entities.
3. The best match is answered with a cited evidence chain (2-hop walk over edges) + confidence score.
4. If the chain contains a `supersedes` edge, the answer flags the old decision as overridden.
5. If no term matches, the match is too weak, or the best match has an empty chain, it refuses instead of inventing.

## 2. Architecture + data flow

```
gh CLI (ingest.py) ─┐
Trac HTML scrape (trac.py) ─┼─► GraphStore (graph.py, SQLite, 2 tables) ─► ask() (qa.py) ─► CLI (cli.py, JSON out)
DEP .rst files (deps.py) ───┘
```

- `whycode/graph.py` (83 lines): `GraphStore`. Two tables, `entities(id, kind, title, body, url, created_at)` and `edges(src, dst, relation)`. Entity kinds: commit, pr, issue, file, function, person, incident, doc. Relations: authored, fixes, references, supersedes, mentions, touches, decides. Stdlib only, no dependencies.
- `whycode/ingest.py` (159 lines): GitHub via `gh api` (authed as eres0045, 5,000/hr). Pulls recent issues/PRs/commits, links by `#NNN` in text: `fixes` if the text says fixes/closes/resolves, else `references`. File detail only for the 30 most-connected commits. Defaults: 200 commits / 100 issues / 100 PRs.
- `whycode/trac.py` (128 lines): Django decisions live in Trac, not GitHub issues, so commit messages like "Fixed #37089" point at Trac. Fetches `code.djangoproject.com/ticket/N` as plain HTML (no auth), parses title/description/first 3 comments with regex. Candidates ranked by how often the number appears in commit messages. PR bodies deliberately excluded (they mix GitHub PR numbers that 404 on Trac).
- `whycode/deps.py` (123 lines): Django Enhancement Proposals from a local `django/deps` checkout become `doc` entities (id is the filename slug, e.g. `dep:0009-async`, because numbers are reused across statuses). `mentions` edges to file entities the DEP text names — literal path or dotted module form only, and only where the file already exists in the graph.
- `whycode/qa.py` (131 lines): tokenise question → find entities by whole-word token match → rank → build 2-hop evidence chain → answer or refuse.
- `whycode/cli.py` (23 lines): thin wrapper, prints the result as JSON.

Demo DB `data/whycode.db` (1.3 MB, built 29 Oct): 678 entities, 641 edges.
Entities: 200 commit, 100 pr, 100 issue, 161 file, 90 person, 27 doc.
Edges: authored 300, fixes 79, references 70, mentions 11, touches 181, **supersedes 0**.

## 3. How confidence, supersession and refusal actually work

`whycode/qa.py`, function `ask()`:

- **Tokenising** (`tokens()`, qa.py:20): lowercase, split on `[a-z0-9_]+`, drop stopwords (why/is/the/does/how/use/uses/used/using/...) and 1-letter tokens. Note: "use" is a stopword, so "why does Django use X" never matches on "use".
- **Matching** (`graph.py:find_by_tokens`): whole-word match only — substring hits do not count ("use" inside "users" is not a match). Score = number of question tokens found in title+body. Full table scan every query (no index; fine at 678 rows).
- **Ranking** (qa.py:75-90): token count first, then title hits (terms in the title beat terms merely mentioned in the body), then evidence-chain size, then entity-id order. This tie-break order was a real bug fix on 29 Oct: a mailers DEP mentioning "Python 3.15" in passing used to beat the Trac ticket actually titled "Python 3.15 compatibility".
- **Confidence** (qa.py:91): `min(0.99, matched_tokens / total_tokens)`. Pure token coverage — it says nothing about evidence quality. A 0.99 can still refuse (see below).
- **Refusal** — four separate rules, all in `ask()`:
  1. No tokens left after stopword removal → refuse.
  2. Any question term appears in NO entity at all → refuse ("The term 'X' appears in no ingested record."). This is what stops "why does Django use microservices?" from being answered off generic matches — except see the DEP 0009 case below.
  3. Confidence < 0.35 (`WEAK`, qa.py:28) → refuse ("Closest match was too weak.").
  4. Best match has an EMPTY evidence chain → refuse ("has no linked records, so there is no evidence chain"). This is the guard that keeps DEP 0009 (mentions "microservices" in passing, zero edges) from answering at 0.99.
- **Supersession** (qa.py:101-106): if any evidence record has relation `supersedes`, the answer adds "Note: this decision was superseded by: ...". **But no code path ever creates a `supersedes` edge.** The live DB has zero of them. Only the synthetic test fixture (`tests/test_core.py:demo_store`) has one. The feature is real in code, fake in data — see §5, gap #1.

Verified demo questions (all re-run 21 Nov, see §8):
- "Why does ignore_warnings match substrings by default?" → answered, 0.99, 8 evidence records. Best match commit `2d9d619676e2`, fixes Trac #37089.
- "Why does Django use microservices?" → refused. Best match DEP 0009, empty chain.
- "Why is Python 3.15 compatibility being added?" → answered, 0.99, 25 evidence records (per docs/demo-qa.md; not re-run today).
- "Why does Django have a simplified routing syntax?" → answered, 0.99, 3 evidence records, best match DEP 0201 (per docs/demo-qa.md; not re-run today).

## 4. What is strong

- **The refusal rules are genuinely good and tested.** Four independent guards, each with a unit test, each closing a real failure mode found during the build (microservices, passing mentions, weak matches). This is the most defensible part of the system — lead the demo with the refusal, it is what "won't hallucinate" actually means.
- **Whole-word matching + title-hit tie-breaks.** Deliberate, documented choices that fix real ranking bugs. Judges who ask "why not just grep?" get a real answer.
- **Linking rules are derived from the repo's own text, never invented.** `#NNN` → fixes vs references by verb; Trac candidates only from commit messages (PR bodies excluded for a stated reason); DEP mentions only to files that already exist. Every edge is traceable.
- **Zero-dependency runtime.** Stdlib only. The bundled DB means the demo runs with no API calls, no credentials, no network. Nothing to fail on stage.
- **13/13 tests green, fast (0.008s).** Fixture-based, no network. `tests/test_core.py` (9), `tests/test_ingest.py` (3), `tests/test_trac.py` (1).
- **Honest docs.** `docs/demo-qa.md` records limits plainly (file-level not function-level, thin DEP chains, SQLite not Neo4j) and the ranking-fix history. Don't lose this tone tonight.

## 5. Gaps and weak spots

1. **Supersession is advertised but has no real data (biggest gap).** `qa.py:101` checks for `supersedes` edges; `ingest.py`, `trac.py`, `deps.py` never create one. DB count: 0. The problem statement explicitly asks for supersession/override detection. A judge who asks "show me an overridden decision" gets nothing. Fix is cheap (§6, P2).
2. **Evidence chains contain noise.** The 2-hop walk (`qa.py:evidence_chain`, qa.py:33) follows ALL relations, including `authored`. The verified Q1 answer's 8 records include an unrelated PR (`pr:22125`, "Added gettext to PATH in Windows CI") that shares only an author, and the best-match commit appears in its own chain twice. "8 linked records" overstates the real evidence. Fix: exclude `authored` from hop-2 expansion, drop the match entity from its own chain (§6, P4).
3. **Function-level entities don't exist.** `graph.py` docstring lists `function` kind and `decides` relation; nothing creates either. Entities are file-level only. "Why is this function like this?" cannot be answered. `docs/demo-qa.md` admits it. Fix: tree-sitter (§6, P5).
4. **CLI only — no UI.** Judges must watch a terminal printing JSON. For a finale where "only a live working product counts", a web UI with a clickable evidence chain + graph view is the single biggest demo upgrade (§6, P1).
5. **Ranking is raw token count.** No term weighting: a rare term ("ignore_warnings") counts the same as a common one ("django"). BM25/TF-IDF would rank better and is a one-hour change (§6, P3).
6. **Snapshot ingestion, no refresh.** Only the most recent 200 commits / 100 PRs / 100 issues. No incremental update, no "ingest any repo" path in the demo. `trac.py` re-fetches HTML every run (no cache). Rebuilding the DB from scratch costs real API calls (gh 5,000/hr authed is fine; Trac is unauthenticated HTML scraping, slow and regex-brittle if Django changes its Trac templates).
7. **DEP answers are thin.** 27 DEPs ingested, only 11 `mentions` edges total — most DEPs have zero edges, so doc answers either refuse or ride on a 1–3 record chain. DEP 0201's chain is 3 records.
8. **No index, full scan per question.** `find_by_tokens` loads every entity and regex-tokenises title+body on every call. Fine at 678 rows, will crawl at 10k+ rows. BM25 (§6, P3) fixes this as a side effect.
9. **Stale lines in docs.** `README.md` still says "Target public repo: pending Ronit's pick" — it's django/django, picked 29 Oct. `README.md` also lists Anshul Kamthe on the team — he is not attending the finale. Fix both in 5 minutes.
10. **Repo hygiene.** `git status` is clean except two untracked dirs: `docs/ai-to-pptx-deck/backend/` and `docs/ai-to-pptx-deck/tool/` (embedded repos with their own `.git`, swept in accidentally, commit dd43527). They are NOT in git. Do not add them; exclude them from any source ZIP. Local HEAD == origin/main at `074bee8`, 0 ahead / 0 behind (verified after `git fetch`).

## 6. Ranked finale build priorities (22h budget)

Total: 14:00 Sat → 12:00 Sun. Reserve ~2h for deck/video/polish + 1h buffer. Work in parallel: Ronit on P1 (UI), Udita on P2+P4, integrate, then P3, then P5 if time.

| # | Work | Why | Effort |
|---|------|-----|--------|
| P1 | **Flask web UI + pyvis graph view.** One page: question box → answer card (confidence, best match, superseded banner) → clickable evidence chain (each record links to its GitHub/Trac URL) → interactive graph of the chain (pyvis). Serve the bundled DB; `flask run` on localhost. This is what the judges actually see. | Biggest demo impact; turns a terminal tool into a product | 4–5h |
| P2 | **Real `supersedes` edges from DEPs.** Parse "Superseded by DEP NNNN" in DEP text + the `superseded/` status dir in `deps.py` → `supersedes` edge old DEP → new DEP. Also: commit messages starting "Reverts" → `supersedes` edge new commit → reverted commit. Then demo it: ask about a superseded DEP and show the banner. | Closes gap #1; the feature exists in code with zero data | 1–2h |
| P3 | **BM25 ranking.** Replace raw token-count ranking with BM25 over title+body (title weighted 2×). Hand-roll it in stdlib (~60 lines, no new dependency) or use `rank-bm25` (Apache-2.0, `pip install rank_bm25`). Keep all four refusal rules untouched. Add a test that the Python 3.15 ticket still beats the mailers DEP. | Better answers, no new risk | 1–2h |
| P4 | **Evidence-chain cleanup.** In `evidence_chain` (qa.py:33): don't expand `authored` edges on hop 2, and drop the best-match entity from its own chain. Re-run the demo questions and update the counts in `docs/demo-qa.md`. | Makes "8 evidence records" honest | ~1h |
| P5 | **tree-sitter function entities.** Parse the Django source tree (clone at venue) with `tree-sitter` + `tree-sitter-python` (both MIT, prebuilt wheels). New `function` entities + `defines` edges file→function, `touches` edges commit→function for changed functions. Enables "why is this function like this?" | Closes gap #3; the docs promise it as "next" | 3–4h |
| P6 | **Neo4j AuraDB mirror (stretch, partner track).** Keep SQLite as the source of truth. Add `whycode/neo4j_export.py`: mirror entities+edges to AuraDB Free ($0, no card, 200k nodes / 400k rels — the graph is 678 nodes) with the official `neo4j` driver (Apache-2.0). Demo the same question in Neo4j Bloom/Browser. Do NOT migrate the store — SQLite stays primary. | Neo4j partner track; visual Cypher demo | 3–4h |
| P7 | **Live re-ingest from the UI.** Repo URL box → runs `ingest.py` + `trac.py` into a fresh DB → answers questions on it. "Ingest any public repo live on stage" is a strong demo moment. Needs `gh` authed on the demo machine — verify early. | Proves it generalises beyond Django | ~2h |

**Do NOT attempt tonight:**
- `sentence-transformers` embeddings (Apache-2.0, but needs PyTorch ~800MB+ install and a ~90MB model download; venue wifi + CPU inference will eat the night). BM25 (P3) is the right retrieval upgrade for 22h.
- `sqlite-vec` (MIT/Apache-2.0) — needs embeddings first; useless without them.
- PyGithub (LGPL-3.0 — copyleft, avoid). The `gh` CLI already does live ingestion; no new client needed.
- Neo4j Community Edition self-host (GPLv3 — avoid). If you do Neo4j, use AuraDB Free (hosted service) + the Apache-2.0 driver, never a self-hosted Community instance.
- Rebuilding the whole ingestion pipeline. It works; extend it, don't rewrite it.

**After every change:** run `python3 -m unittest discover -s tests` — all 13 must stay green. Add a test for each new behaviour (supersedes edge, BM25 tie-break, chain without authored noise).

## 7. Open-source shortlist (all verified 21 Nov, $0)

| Library | What it adds here | License | Cost | Effort |
|---|---|---|---|---|
| Flask (`pip install flask`, 3.1.3) | Web UI for the demo (P1) | BSD-3-Clause | $0 | 4–5h with UI |
| pyvis (`pip install pyvis`, 0.3.2) | Interactive evidence-chain graph in one HTML file (P1) | BSD-3-Clause | $0 | ~1h inside P1 |
| tree-sitter + tree-sitter-python (`pip install tree-sitter tree-sitter-python`, 0.26.x) | Real code-structure parsing → function entities (P5) | MIT / MIT | $0 | 3–4h |
| rank-bm25 (`pip install rank_bm25`, 0.2.2) | BM25 ranking (P3). Upstream unmaintained since 2022; hand-rolled stdlib BM25 is equally good and has zero install risk | Apache-2.0 | $0 | 1–2h |
| neo4j driver (`pip install neo4j`, 6.4.1) + AuraDB Free | Neo4j mirror + partner track (P6) | Apache-2.0 (driver); AuraDB Free $0, no card, 200k nodes / 400k rels | $0 | 3–4h |
| NetworkX (`pip install networkx`) | Graph analytics if needed (centrality/PageRank to weight evidence) — optional, only if P3 wants it | BSD-3-Clause | $0 | ~1h |
| sentence-transformers (Apache-2.0) | Semantic search — **skip tonight** (torch + 90MB model, too heavy for the venue) | Apache-2.0 | $0 | 4h+ — no |
| sqlite-vec (MIT/Apache-2.0) | Vector search inside SQLite — **skip** (needs embeddings first) | MIT / Apache-2.0 | $0 | — |

Licences to avoid here: anything GPL/AGPL/LGPL (PyGithub LGPL-3.0, Neo4j Community GPLv3). Everything recommended above is MIT/Apache-2.0/BSD.

## 8. Exact commands

```text
# Tests (must stay 13/13 green after every change)
python3 -m unittest discover -s tests

# Demo — answer with evidence chain
python3 -m whycode.cli --db data/whycode.db --question "Why does ignore_warnings match substrings by default?"
# → answered, confidence 0.99, 8 evidence records (before P4 cleanup)

# Demo — honest refusal
python3 -m whycode.cli --db data/whycode.db --question "Why does Django use microservices?"
# → refused, best match DEP 0009 has no evidence chain

# Demo — design-doc answer
python3 -m whycode.cli --db data/whycode.db --question "Why does Django have a simplified routing syntax?"
# → answered, confidence 0.99, best match DEP 0201

# Demo — ranking tie-break (ticket beats passing DEP mention)
python3 -m whycode.cli --db data/whycode.db --question "Why is Python 3.15 compatibility being added?"
# → answered, 0.99, 25 evidence records

# Rebuild the DB from scratch (needs gh authed + network; ~10 min)
python3 -m whycode.ingest --repo django/django --db data/whycode.db
python3 -m whycode.trac --db data/whycode.db --limit 100
# DEPs need a local django/deps checkout:
python3 -m whycode.deps --db data/whycode.db --deps-dir <path-to-django/deps>

# DB inspection
sqlite3 "file:data/whycode.db?mode=ro" "SELECT kind, COUNT(*) FROM entities GROUP BY kind;"
sqlite3 "file:data/whycode.db?mode=ro" "SELECT relation, COUNT(*) FROM edges GROUP BY relation;"

# Git (verified 21 Nov ~11:00 IST: HEAD == origin/main 074bee8, clean apart from 2 untracked dirs)
git fetch origin && git status --short
```

## 9. Tonight's order of work (suggested)

1. 14:00–14:30 — Both: read this file + `docs/demo-qa.md`, run the 4 demo questions above, pick the split. Fix the two stale README lines (5 min).
2. 14:30–18:30 — Ronit: P1 UI skeleton (Flask route + question box + answer card). Udita: P2 supersedes edges + a test. Commit after each piece, tests green.
3. 18:30–20:00 — P4 chain cleanup + P3 BM25. Re-run demo questions, update counts in `docs/demo-qa.md`.
4. 20:00–21:00 — Integrate UI + graph view (pyvis). First full live demo run-through, both watching.
5. 21:00–00:00 — P5 tree-sitter if P1–P4 are solid; else polish + second repo ingest (P7-lite: pre-ingest a second small repo as a backup demo).
6. 00:15–07:00 — Overnight: P6 Neo4j mirror only if everything above is done and tested. Otherwise: deck + video refresh + rehearsal. Do not start anything new after 04:00.
7. 07:00–12:00 Sun — Freeze prep: full test run, demo rehearsal x3, source ZIP rebuilt (exclude `docs/ai-to-pptx-deck/backend` + `tool`), repo public, push, verify live.

## 10. Verification log (21 Nov 2026, this machine)

- `python3 -m unittest discover -s tests` → 13/13 OK in 0.008s.
- Q1 ignore_warnings → answered 0.99, 8 evidence, commit `2d9d619676e2` → Trac #37089. Matches `docs/demo-qa.md`.
- Q2 microservices → refused, "Best match 'DEP 0009: Async-capable Django' has no linked records". Matches `docs/demo-qa.md`.
- DB: 678 entities / 641 edges, `supersedes` count 0 (checked by query).
- `git fetch origin`: HEAD `074bee8` == origin/main, 0 ahead / 0 behind. Untracked: `docs/ai-to-pptx-deck/backend/`, `docs/ai-to-pptx-deck/tool/`.
- All open-source entries in §7 were verified on PyPI/GitHub on 21 Nov (licence + version + cost). Nothing in this file is invented.
