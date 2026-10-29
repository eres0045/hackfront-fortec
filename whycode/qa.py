"""WhyCode QA: answer "why" questions from the graph, or refuse.

Rules, enforced here and not in the prompt:
- Every claim in an answer must trace to a graph entity in the evidence chain.
- If no entity matches the question, or the best match is too weak, the
  answer is a refusal, never an invention.
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


def ask(store, question):
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
    best_count, best, matched = ranked[0]
    confidence = round(min(0.99, best_count / len(toks)), 2)
    if confidence < WEAK:
        return {"question": question, "refused": True,
                "reason": REFUSAL + " Closest match was too weak.",
                "confidence": confidence, "evidence": []}
    evidence = []
    seen = set()
    frontier = [best["id"]]
    for _ in range(2):
        nxt = []
        for eid in frontier:
            for nb in store.neighbors(eid):
                key = (eid, nb["id"], nb["relation"], "out")
                if key in seen:
                    continue
                seen.add(key)
                evidence.append({
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
                    "from": nb["id"],
                    "relation": nb["relation"],
                    "title": nb["title"],
                    "kind": nb["kind"],
                    "url": nb["url"],
                    "direction": "in",
                })
                nxt.append(nb["id"])
        frontier = nxt
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
