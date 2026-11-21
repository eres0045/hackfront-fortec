"""WhyCode features: blast-radius, freshness, load-bearing, grades, who-to-ask.

All of these read the graph through the store abstraction
(`GraphStore` / `Neo4jGraphStore`), so they work identically on
SQLite and on the Neo4j mirror — the same store methods, the same
ordering rules, the same results. Nothing here writes to the graph.

Honesty rules, enforced in code:
- Blast radius walks the graph outward from the decision. Files come
  first (touches / mentions edges), but only 30 of the 200 commits
  carry file detail, so a file-only walk is EMPTY for the two main
  demo questions (the ignore_warnings commit touches no file in the
  graph, the steering DEPs mention none). The walk therefore also
  follows commits / issues / PRs reached through the evidence chain
  itself — every entity it reports is still a real graph neighbour,
  never a text guess. A category with nothing in it is omitted, and
  the card is skipped entirely when the walk finds nothing at all.
- Freshness shows facts only, never a verdict. "Decided 2019-05-06.
  The code it governs changed 14 times since, last 2024-11-02." is
  a fact; "probably stale" would be a judgement, and is never
  stated. When the decision has no date, or no governed files in
  the graph, the freshness line is omitted entirely — never guessed.
- Evidence grades are a stated rule, not a judgement call:
  A = doc/DEP (formal decision record), B = PR (reviewed change),
  C = commit (implementation), D = issue/ticket (request /
  discussion). Person and file entities are not evidence records
  and are never graded.
- PageRank (load-bearing decisions) runs on the whole directed
  graph with a stdlib power-iteration implementation in this module.
  NetworkX's pagerank was tried first and dropped: it needs numpy
  AND scipy, a ~40MB binary dependency for a 25-line algorithm the
  codebase can carry itself (its BM25 is hand-rolled stdlib for the
  same reason). A decision is load-bearing when many other records
  point at it; the score is shown, so the ranking can be checked.
"""
from whycode.qa import _dep_created_at

MAX_FILES_SHOWN = 8
MAX_COMMITS_SHOWN = 10
MAX_ISSUES_SHOWN = 10
MAX_DECISIONS_SHOWN = 5

# Evidence grade: (letter, what the grade means). Stated rule — see
# the module docstring. Person/file entities are not evidence and
# get no grade (evidence_grade returns None for them).
EVIDENCE_GRADES = {
    "doc": ("A", "formal decision record"),
    "pr": ("B", "reviewed change"),
    "commit": ("C", "implementation"),
    "issue": ("D", "request / discussion"),
}


def evidence_grade(rec):
    """(letter, label) for an evidence record, or None (not evidence)."""
    return EVIDENCE_GRADES.get(rec.get("kind"))


def _decision_date(entity):
    """The date a decision was made: created_at, or a DEP's :Created:.

    Docs carry no created_at in the graph — the date lives in the DEP
    body. Returns "YYYY-MM-DD" or "".
    """
    date = (entity.get("created_at") or "")[:10]
    if date:
        return date
    return _dep_created_at(entity)


def governed_files(store, match, evidence=None):
    """Files a decision governs, as an {id: entity} dict.

    Sources, in order: the match itself when it is a file; file
    entities in the evidence chain; files the match touches /
    mentions; files touched / mentioned by evidence commits / docs;
    files touched by commits that fix or reference the match or an
    evidence issue / PR (those commits' files are the code the
    decision governs). Only files that exist as entities in the
    graph are returned — a path mentioned in prose but absent from
    the graph is not a governed file.
    """
    files = {}

    def _add(ent):
        if ent and ent.get("kind") == "file":
            files[ent["id"]] = ent

    _add(match)

    evidence = evidence or []
    for rec in evidence:
        if rec.get("kind") == "file":
            _add(store.get_entity(rec["id"]))
    for rel in ("touches", "mentions"):
        for nb in store.neighbors(match["id"], rel):
            _add(nb)
    seeds = [match]
    for rec in evidence:
        ent = store.get_entity(rec["id"]) if rec.get("id") else None
        if not ent:
            continue
        seeds.append(ent)
        if ent["kind"] == "commit":
            for nb in store.neighbors(ent["id"], "touches"):
                _add(nb)
        elif ent["kind"] == "doc":
            for nb in store.neighbors(ent["id"], "mentions"):
                _add(nb)
    for ent in seeds:
        for nb in store.neighbors_reverse(ent["id"]):
            if nb.get("kind") == "commit" and nb.get("relation") in (
                    "fixes", "references"):
                for f in store.neighbors(nb["id"], "touches"):
                    _add(f)
    return files


def blast_radius(store, match, evidence=None, max_files=MAX_FILES_SHOWN,
                 max_commits=MAX_COMMITS_SHOWN,
                 max_issues=MAX_ISSUES_SHOWN,
                 max_decisions=MAX_DECISIONS_SHOWN):
    """Walk the graph outward from a decision; what breaks if it changes.

    Returns counts plus capped display lists. Files first (the code
    the decision governs); then commits touching those files, commits
    in the evidence chain, and commits fixing / referencing the
    decision or its evidence issues; issues / PRs in the chain and
    fixed / referenced by those commits; related decisions (docs in
    the chain — never the decision itself); people who authored those
    commits, ranked by how many they authored. Lists are capped for
    display; the counts are the full totals.
    """
    evidence = evidence or []
    files = governed_files(store, match, evidence)

    commits = {}

    def _add_commit(ent):
        if ent and ent.get("kind") == "commit":
            commits[ent["id"]] = ent

    for fid in files:
        for nb in store.neighbors_reverse(fid):
            if nb.get("kind") == "commit" and nb.get("relation") == "touches":
                _add_commit(nb)
    for rec in evidence:
        if rec.get("kind") == "commit":
            _add_commit(store.get_entity(rec["id"]))
    if match.get("kind") == "commit":
        _add_commit(match)
    seeds = [match]
    for rec in evidence:
        ent = store.get_entity(rec["id"]) if rec.get("id") else None
        if ent:
            seeds.append(ent)
    for ent in seeds:
        for nb in store.neighbors_reverse(ent["id"]):
            if nb.get("kind") == "commit" and nb.get("relation") in (
                    "fixes", "references"):
                _add_commit(nb)

    issues = {}
    for rec in evidence:
        if rec.get("kind") in ("issue", "pr"):
            ent = store.get_entity(rec["id"])
            if ent:
                issues[ent["id"]] = ent
    for cid in list(commits):
        for nb in store.neighbors(cid):
            if nb.get("kind") in ("issue", "pr") and nb.get("relation") in (
                    "fixes", "references"):
                issues[nb["id"]] = nb

    decisions = {}
    for rec in evidence:
        if rec.get("kind") == "doc":
            ent = store.get_entity(rec["id"])
            if ent:
                decisions[ent["id"]] = ent

    people = {}
    for cid in commits:
        for nb in store.neighbors(cid, "authored"):
            if nb.get("kind") == "person":
                people[nb["id"]] = people.get(nb["id"], 0) + 1
    people_ranked = sorted(
        ({"id": pid, "title": store.get_entity(pid)["title"], "count": n}
         for pid, n in people.items()
         if store.get_entity(pid)),
        key=lambda p: (-p["count"], p["title"]))

    commit_list = sorted(
        commits.values(), key=lambda c: c.get("created_at") or "",
        reverse=True)
    return {
        "files": sorted(files.values(), key=lambda f: f["id"])[:max_files],
        "file_count": len(files),
        "commits": commit_list[:max_commits],
        "commit_count": len(commits),
        "issues": sorted(issues.values(),
                         key=lambda i: i["id"])[:max_issues],
        "issue_count": len(issues),
        "decisions": sorted(decisions.values(),
                            key=lambda d: d["id"])[:max_decisions],
        "decision_count": len(decisions),
        "people": people_ranked,
        "total": len(files) + len(commits) + len(issues) + len(decisions),
    }


def who_to_ask(blast, top_n=2):
    """Top people for a blast radius, by commits authored. Names only,
    from the graph — never invented."""
    return blast.get("people", [])[:top_n]


def decision_freshness(store, match, evidence=None):
    """The groundable freshness signal for one decision, or None.

    Decision date from created_at (or a DEP's :Created: header).
    Churn = commits with a date AFTER the decision date that touch
    the files it governs. Returns the facts (date, churn, last
    change, and the display line) — never a verdict. None when the
    decision has no date or no governed files in the graph: there is
    nothing groundable to say, so nothing is said.
    """
    date = _decision_date(match)
    if not date:
        return None
    files = governed_files(store, match, evidence)
    if not files:
        return None
    churn = {}
    for fid in files:
        for nb in store.neighbors_reverse(fid):
            if nb.get("kind") == "commit" and nb.get("relation") == "touches":
                cdate = (nb.get("created_at") or "")[:10]
                if cdate and cdate > date:
                    churn[nb["id"]] = nb
    last = max(((nb.get("created_at") or "")[:10]
                for nb in churn.values()), default=None)
    n = len(churn)
    if n == 0:
        line = (f"Decided {date}. No changes to its code since it was "
                f"decided.")
    else:
        line = (f"Decided {date}. The code it governs changed {n} "
                f"{'time' if n == 1 else 'times'} since, last {last}.")
    return {"date": date, "file_count": len(files), "churn": n,
            "last_change": last, "line": line}


def _pagerank(nodes, edges, alpha=0.85, tol=1e-6, max_iter=100):
    """PageRank by power iteration, stdlib only.

    The same algorithm NetworkX runs (damping alpha, dangling nodes
    redistributed evenly), in ~25 lines — no numpy/scipy, so the
    deploy stays binary-free. Scores sum to 1.
    """
    nodes = list(nodes)
    n = len(nodes)
    if n == 0:
        return {}
    out = {node: [] for node in nodes}
    for src, dst in edges:
        if src in out and dst in out:
            out[src].append(dst)
    in_links = {node: [] for node in nodes}
    for src, dsts in out.items():
        if not dsts:
            continue
        w = 1.0 / len(dsts)
        for dst in dsts:
            in_links[dst].append((src, w))
    rank = {node: 1.0 / n for node in nodes}
    for _ in range(max_iter):
        dangling = sum(rank[node] for node in nodes if not out[node])
        base = (1.0 - alpha) / n + alpha * dangling / n
        new, err = {}, 0.0
        for node in nodes:
            s = base
            for src, w in in_links[node]:
                s += alpha * rank[src] * w
            new[node] = s
            err += abs(s - rank[node])
        rank = new
        if err < tol:
            break
    return rank


def load_bearing(store, top_n=10):
    """Top decisions by PageRank over the whole directed graph.

    A decision is load-bearing when many other records point at it.
    Only kind=doc entities are ranked. Each row carries the score
    (so the ranking is checkable), the decision date when the graph
    has one, and how many records link to it.

    A history-only graph (a bring-your-own repo) has no docs: the
    same ranking then runs over commits, so the page still answers
    "what shaped this codebase?" instead of coming back empty.
    """
    entities = {e["id"]: e for e in store.all_entities()}
    edges = [(e["src"], e["dst"]) for e in store.all_edges()]
    scores = _pagerank(entities, edges)
    degree = {eid: 0 for eid in entities}
    for src, dst in edges:
        if src in degree:
            degree[src] += 1
        if dst in degree:
            degree[dst] += 1
    docs = [e for e in entities.values() if e["kind"] == "doc"]
    kind = "doc"
    if not docs:
        docs = [e for e in entities.values() if e["kind"] == "commit"]
        kind = "commit"
    docs.sort(key=lambda e: -scores.get(e["id"], 0.0))
    return [{
        "id": ent["id"],
        "title": ent["title"],
        "url": ent.get("url") or "",
        "score": round(scores.get(ent["id"], 0.0), 4),
        "date": _decision_date(ent),
        "date_label": "decided" if kind == "doc" else "landed",
        "kind": kind,
        "links": degree.get(ent["id"], 0),
    } for ent in docs[:top_n]]


def decision_health(store, top_n=10):
    """Every dated decision, ranked by how much its code moved since.

    Churn = commits after the decision date touching its governed
    files (see decision_freshness). Ranked by churn, then by most
    recent change. Decisions with no files recorded in the graph
    carry churn 0 and sort to the bottom — the table says so, rather
    than hiding them. Only dated decisions appear: an undated one
    cannot be ranked on staleness.
    """
    rows = []
    cands = [ent for ent in store.all_entities()
             if ent.get("kind") == "doc"]
    kind = "doc"
    if not cands:
        # History-only graph (bring-your-own repo): rank commits.
        cands = [ent for ent in store.all_entities()
                 if ent.get("kind") == "commit"]
        kind = "commit"
    for ent in cands:
        date = _decision_date(ent)
        if not date:
            continue
        fresh = decision_freshness(store, ent, evidence=[])
        rows.append({
            "id": ent["id"],
            "title": ent["title"],
            "url": ent.get("url") or "",
            "date": date,
            "date_label": "decided" if kind == "doc" else "landed",
            "kind": kind,
            "file_count": fresh["file_count"] if fresh else 0,
            "churn": fresh["churn"] if fresh else 0,
            "last_change": fresh["last_change"] if fresh else None,
        })
    # Two stable passes: most recent change first, then most churn.
    rows.sort(key=lambda r: r["last_change"] or "", reverse=True)
    rows.sort(key=lambda r: r["churn"], reverse=True)
    return rows[:top_n]


def digest(store, top_n=10):
    """The monthly digest: new decisions, what changed, top experts.

    All three sections are computed from the graph as it stands —
    "new" means most recently dated, not "since last month" (the
    graph is a snapshot; there is no previous digest to diff
    against, and inventing one would be fabrication). New decisions
    are docs by decision date, most recent first; what changed is
    commits by created_at, most recent first; top experts are people
    ranked by commits authored.
    """
    entities = store.all_entities()
    docs = []
    for ent in entities:
        if ent.get("kind") != "doc":
            continue
        date = _decision_date(ent)
        if not date:
            continue
        docs.append({"id": ent["id"], "title": ent["title"],
                     "url": ent.get("url") or "", "date": date})
    docs.sort(key=lambda d: d["date"], reverse=True)
    changes = [{
        "id": ent["id"], "title": ent["title"],
        "url": ent.get("url") or "",
        "date": (ent.get("created_at") or "")[:10],
    } for ent in entities if ent.get("kind") == "commit"
        and ent.get("created_at")]
    changes.sort(key=lambda c: c["date"], reverse=True)
    authored = {}
    for edge in store.all_edges():
        if edge.get("relation") == "authored":
            authored[edge["dst"]] = authored.get(edge["dst"], 0) + 1
    people = {e["id"]: e for e in entities if e.get("kind") == "person"}
    experts = sorted(
        ({"id": pid, "title": people[pid]["title"], "commits": n}
         for pid, n in authored.items() if pid in people),
        key=lambda p: (-p["commits"], p["title"]))
    return {
        "new_decisions": docs[:top_n],
        "recent_changes": changes[:top_n],
        "top_experts": experts[:top_n],
    }
