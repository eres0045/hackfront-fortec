"""WhyCode QA: answer "why" questions from the graph, or refuse.

Rules, enforced here and not in the prompt:
- Every claim in an answer must trace to a graph entity in the evidence chain.
- If no entity matches the question, or the best match is too weak, the
  answer is a refusal, never an invention.
- Ranking: matched-token count first, then title hits (a record whose
  TITLE is about the question beats one that merely mentions it), then
  evidence-chain size, then entity-id order as a last resort. Id order
  alone once let a mailers doc that mentions Python 3.15 in passing beat
  the Trac ticket titled "Python 3.15 compatibility."
- A best match with an empty evidence chain is a refusal, not an answer:
  a claim with zero linked records behind it is not an evidenced answer.
  This is what keeps a passing mention (DEP 0009 on "microservices")
  from answering at 0.99 with nothing behind it.
- If the evidence chain contains a supersedes edge, the answer says the
  old decision was overridden and points at the newer one.
"""
import re

STOPWORDS = {
    "why", "is", "the", "a", "an", "does", "do", "did", "this", "that",
    "it", "its", "in", "on", "of", "to", "for", "how", "what", "was",
    "were", "are", "be", "been", "with", "by", "from", "as", "and", "or",
    "use", "uses", "used", "using", "being",
}

REFUSAL = "No evidence in the graph answers this. Refusing to invent an answer."
WEAK = 0.35


def tokens(question):
    return [t for t in re.findall(r"[a-z0-9_]+", question.lower())
            if t not in STOPWORDS and len(t) > 1]


def evidence_chain(store, entity_id):
    """2-hop evidence walk (outgoing and incoming edges), deduplicated."""
    evidence = []
    seen = set()
    frontier = [entity_id]
    for _ in range(2):
        nxt = []
        for eid in frontier:
            for nb in store.neighbors(eid):
                key = (eid, nb["id"], nb["relation"], "out")
                if key in seen:
                    continue
                seen.add(key)
                evidence.append({
                    "id": nb["id"],
                    "from": eid,
                    "relation": nb["relation"],
                    "title": nb["title"],
                    "kind": nb["kind"],
                    "url": nb["url"],
                    "direction": "out",
                })
                nxt.append(nb["id"])
            for nb in store.neighbors_reverse(eid):
                key = (nb["id"], eid, nb["relation"], "in")
                if key in seen:
                    continue
                seen.add(key)
                evidence.append({
                    "id": nb["id"],
                    "from": nb["id"],
                    "relation": nb["relation"],
                    "title": nb["title"],
                    "kind": nb["kind"],
                    "url": nb["url"],
                    "direction": "in",
                })
                nxt.append(nb["id"])
        frontier = nxt
    return evidence


def _dep_created_at(entity):
    """Date a DEP was created, from its `:Created:` header field.

    Docs carry no created_at in the graph; the date lives in the DEP
    body itself. Returns "YYYY-MM-DD" or "".
    """
    if entity.get("kind") != "doc":
        return ""
    m = re.search(r":Created:\s*(\d{4}-\d{2}-\d{2})", entity.get("body") or "")
    return m.group(1) if m else ""


def decision_timeline(store, match, evidence):
    """Dated events for a decision, oldest first — the decision's life story.

    Every event needs a real date: commits/PRs carry created_at, DEPs
    carry :Created: in their body. Entities with no date are omitted,
    never guessed. A supersedes edge marks the newer entity's event.
    """
    newer_ids = set()
    for rec in evidence:
        if rec["relation"] != "supersedes":
            continue
        # "out": match -> newer record; "in": older record -> match (newer).
        newer_ids.add(rec["id"] if rec["direction"] == "out" else match["id"])
    events = []
    seen_ids = set()
    ordered = [match] + [store.get_entity(r["id"]) for r in evidence
                         if r.get("id")]
    for ent in ordered:
        if not ent or ent["id"] in seen_ids:
            continue
        seen_ids.add(ent["id"])
        date = ent.get("created_at") or _dep_created_at(ent)
        if not date:
            continue
        kind = ent["kind"]
        if kind == "doc":
            label = "DEP published"
        elif kind == "commit":
            label = "Commit landed"
        elif kind == "pr":
            label = "Pull request"
        elif kind == "issue":
            label = "Ticket opened"
        else:
            label = kind
        if ent["id"] in newer_ids:
            label = "Supersedes an earlier decision"
        events.append({"date": date, "title": ent["title"], "kind": kind,
                       "url": ent.get("url") or "", "label": label})
    # Same (date, title) twice is one event, not two.
    deduped, seen_keys = [], set()
    for ev in events:
        key = (ev["date"], ev["title"])
        if key in seen_keys:
            continue
        seen_keys.add(key)
        deduped.append(ev)
    deduped.sort(key=lambda e: e["date"])
    return deduped


def ask(store, question):
    # "Why not" questions ("why didn't Django do X?") are answered from
    # the DEPs' own Alternatives sections, not from the evidence chain:
    # the record of what was rejected lives in the DEP text itself. If
    # no rejected alternative matches, fall through to the normal path —
    # a why-not phrasing must never refuse a question the normal engine
    # could answer (e.g. "why use X instead of Y?").
    from whycode.alternatives import answer_why_not, is_why_not

    if is_why_not(question):
        why_not = answer_why_not(store, question)
        if not why_not["refused"]:
            return why_not
    toks = tokens(question)
    if not toks:
        return {"question": question, "refused": True, "reason": REFUSAL,
                "confidence": 0.0, "evidence": []}
    # A question term that appears nowhere in the graph means the graph
    # holds no record of what is asked about. That is a refusal, not a
    # licence to answer from the nearest generic match: without this rule,
    # "why does Django use microservices?" was answered from a docs commit
    # merely because it contained the words "Django" and "use".
    for t in toks:
        if not store.find_by_tokens([t]):
            return {"question": question, "refused": True,
                    "reason": REFUSAL + f" The term '{t}' appears in no "
                    "ingested record.",
                    "confidence": 0.0, "evidence": []}
    ranked = store.find_by_tokens(toks)
    if not ranked:
        return {"question": question, "refused": True, "reason": REFUSAL,
                "confidence": 0.0, "evidence": []}
    best_count = ranked[0][0]
    # Token-count ties are broken by evidence quality, not entity id:
    # title hits first, then evidence-chain size, then id order.
    tied = [r for r in ranked if r[0] == best_count]
    scored = []
    for _, ent, matched in tied:
        title_words = set(re.findall(r"[a-z0-9_]+", ent["title"].lower()))
        title_hits = sum(1 for t in toks if t in title_words)
        chain = evidence_chain(store, ent["id"])
        scored.append(((-title_hits, -len(chain), ent["id"]), ent, chain))
    scored.sort(key=lambda s: s[0])
    _, best, evidence = scored[0]
    confidence = round(min(0.99, best_count / len(toks)), 2)
    if confidence < WEAK:
        return {"question": question, "refused": True,
                "reason": REFUSAL + " Closest match was too weak.",
                "confidence": confidence, "evidence": []}
    if not evidence:
        return {"question": question, "refused": True,
                "reason": REFUSAL + f" Best match '{best['title']}' has no "
                "linked records, so there is no evidence chain to answer "
                "from.",
                "confidence": confidence, "evidence": []}
    superseded_by = [e for e in evidence if e["relation"] == "supersedes"]
    lines = [f"Best match: {best['title']} ({best['kind']})."]
    if superseded_by:
        lines.append(
            "Note: this decision was superseded by: "
            + ", ".join(e["title"] for e in superseded_by) + ".")
    lines.append(
        f"Evidence: {len(evidence)} linked record(s) in the chain "
        f"(matched {best_count}/{len(toks)} question terms).")
    return {"question": question, "refused": False,
            "answer": " ".join(lines), "confidence": confidence,
            "evidence": evidence, "match": best}
