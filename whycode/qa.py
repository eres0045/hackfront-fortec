"""WhyCode QA: Dual-Process reasoning architecture.

System 1 (Fast, Non-autoregressive intent routing & calibrated abstention gate)
-> System 2 (Multi-hop graph traversal, evidence chain, supersession detection).
"""
import re
from whycode.system1 import System1Engine, Intent

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
    return evidence


def ask(store, question):
    sys1 = System1Engine(abstain_threshold=WEAK).decide(store, question)
    toks = sys1.tokens

    if sys1.abstain:
        reason_msg = f"{REFUSAL} {sys1.abstain_reason}" if sys1.abstain_reason else REFUSAL
        if "No discriminative keywords" in (sys1.abstain_reason or ""):
            reason_msg = REFUSAL
        elif "Ungrounded query:" in (sys1.abstain_reason or ""):
            m = re.search(r"the term '([^']+)'", sys1.abstain_reason)
            term = m.group(1) if m else "unknown"
            reason_msg = f"{REFUSAL} The term '{term}' appears in no ingested record."

        return {
            "question": question,
            "refused": True,
            "reason": reason_msg,
            "confidence": sys1.confidence,
            "evidence": [],
            "system1": {
                "intent": sys1.intent.value,
                "is_negative": sys1.is_negative_query,
                "abstain": True,
                "confidence": sys1.confidence,
            },
        }

    ranked = store.find_by_tokens(toks)
    if not ranked:
        return {"question": question, "refused": True, "reason": REFUSAL,
                "confidence": 0.0, "evidence": [],
                "system1": {"intent": sys1.intent.value, "abstain": True}}
    best_count = ranked[0][0]
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
                "confidence": confidence, "evidence": [],
                "system1": {"intent": sys1.intent.value, "abstain": True}}
    if not evidence:
        return {"question": question, "refused": True,
                "reason": REFUSAL + f" Best match '{best['title']}' has no "
                "linked records, so there is no evidence chain to answer "
                "from.",
                "confidence": confidence, "evidence": [],
                "system1": {"intent": sys1.intent.value, "abstain": True}}
    superseded_by = [e for e in evidence if e["relation"] == "supersedes"]
    lines = [f"Best match: {best['title']} ({best['kind']})."]
    if superseded_by:
        lines.append(
            "Note: this decision was superseded by: "
            + ", ".join(e["title"] for e in superseded_by) + ".")
    lines.append(
        f"Evidence: {len(evidence)} linked record(s) in the chain "
        f"(matched {best_count}/{len(toks)} question terms).")
    return {
        "question": question,
        "refused": False,
        "answer": " ".join(lines),
        "confidence": confidence,
        "evidence": evidence,
        "match": best,
        "system1": {
            "intent": sys1.intent.value,
            "is_negative": sys1.is_negative_query,
            "abstain": False,
            "confidence": sys1.confidence,
        },
    }
