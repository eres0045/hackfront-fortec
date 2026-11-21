"""WhyCode System 1 Decision Engine: Fast, typed query classification
and calibrated abstention gate.

Implements the Dual-Process cognitive architecture:
- System 1 (Fast, ~1ms, Non-autoregressive heuristics & intent routing):
  Classifies intent (WHY_DECISION, WHY_NOT, SUPERSEDED, UNGROUNDED) and
  applies a calibrated abstention gate before touching the graph.
- System 2 (Deliberative, Multi-hop Graph Traversal in qa.py):
  Executes Cypher/SQLite graph walks, generates evidence chains, and
  verifies overrides/supersessions.
"""

from dataclasses import dataclass
from enum import Enum
import re
from typing import List, Optional, Set


class Intent(str, Enum):
    WHY_DECISION = "why_decision"
    WHY_NOT = "why_not"
    SUPERSEDED = "superseded"
    OUT_OF_SCOPE = "out_of_scope"


@dataclass
class System1Decision:
    intent: Intent
    tokens: List[str]
    is_negative_query: bool
    confidence: float
    abstain: bool
    abstain_reason: Optional[str] = None
    target_topics: Optional[List[str]] = None


STOPWORDS: Set[str] = {
    "why", "is", "the", "a", "an", "does", "do", "did", "this", "that",
    "it", "its", "in", "on", "of", "to", "for", "how", "what", "was",
    "were", "are", "be", "been", "with", "by", "from", "as", "and", "or",
    "use", "uses", "used", "using", "being", "have", "has", "had", "we",
    "they", "there",
}

NEGATIVE_MARKERS = [
    r"\bwhy\s+didn'?t\b",
    r"\bwhy\s+not\b",
    r"\bwhy\s+wasn'?t\b",
    r"\bwhy\s+never\b",
    r"\binstead\s+of\b",
    r"\brejected\b",
]

SUPERSEDED_MARKERS = [
    r"\bsuperseded\b",
    r"\breplaced\b",
    r"\bdeprecated\b",
    r"\boverridden\b",
]


class System1Engine:
    def __init__(self, abstain_threshold: float = 0.35):
        self.abstain_threshold = abstain_threshold

    def extract_tokens(self, text: str) -> List[str]:
        return [
            t for t in re.findall(r"[a-z0-9_]+", text.lower())
            if t not in STOPWORDS and len(t) > 1
        ]

    def classify_intent(self, question: str) -> Intent:
        q_lower = question.lower()
        for pat in NEGATIVE_MARKERS:
            if re.search(pat, q_lower):
                return Intent.WHY_NOT
        for pat in SUPERSEDED_MARKERS:
            if re.search(pat, q_lower):
                return Intent.SUPERSEDED
        if re.search(r"\bwhy\b", q_lower) or re.search(r"\bhow\b", q_lower):
            return Intent.WHY_DECISION
        return Intent.OUT_OF_SCOPE

    def decide(self, store, question: str) -> System1Decision:
        """Single-pass System 1 routing + calibrated abstention check."""
        intent = self.classify_intent(question)
        toks = self.extract_tokens(question)

        # Empty question or no discriminative tokens
        if not toks:
            return System1Decision(
                intent=intent,
                tokens=[],
                is_negative_query=(intent == Intent.WHY_NOT),
                confidence=0.0,
                abstain=True,
                abstain_reason="No discriminative keywords detected in question.",
                target_topics=[],
            )

        # Fast graph presence verification:
        # If any essential query term appears in zero graph records,
        # System 1 immediately abstains (anti-hallucination gate).
        missing_terms = [t for t in toks if not store.find_by_tokens([t])]
        if missing_terms:
            return System1Decision(
                intent=intent,
                tokens=toks,
                is_negative_query=(intent == Intent.WHY_NOT),
                confidence=0.0,
                abstain=True,
                abstain_reason=(
                    f"Ungrounded query: the term '{missing_terms[0]}' "
                    f"appears in no ingested record."
                ),
                target_topics=toks,
            )

        # Rank matches to calculate calibrated preliminary confidence
        ranked = store.find_by_tokens(toks)
        if not ranked:
            return System1Decision(
                intent=intent,
                tokens=toks,
                is_negative_query=(intent == Intent.WHY_NOT),
                confidence=0.0,
                abstain=True,
                abstain_reason="No entities match the query tokens.",
                target_topics=toks,
            )

        best_token_hits = ranked[0][0]
        calibrated_conf = round(min(0.99, best_token_hits / len(toks)), 2)

        if calibrated_conf < self.abstain_threshold:
            return System1Decision(
                intent=intent,
                tokens=toks,
                is_negative_query=(intent == Intent.WHY_NOT),
                confidence=calibrated_conf,
                abstain=True,
                abstain_reason=(
                    f"Confidence {calibrated_conf:.2f} is below calibrated "
                    f"abstention threshold {self.abstain_threshold:.2f}."
                ),
                target_topics=toks,
            )

        return System1Decision(
            intent=intent,
            tokens=toks,
            is_negative_query=(intent == Intent.WHY_NOT),
            confidence=calibrated_conf,
            abstain=False,
            abstain_reason=None,
            target_topics=toks,
        )
