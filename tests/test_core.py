"""Core tests for the WhyCode graph + QA engine (stdlib unittest)."""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from whycode.graph import GraphStore
from whycode.qa import ask


def demo_store():
    s = GraphStore()
    s.add_entity("c1", "commit", "Fix token expiry race in auth refresh",
                 "Refresh raced with expiry; lock the refresh path.", "u/c1")
    s.add_entity("i9", "issue", "Auth tokens expire mid-request",
                 "Users report 401s when a token expires mid-request.", "u/i9")
    s.add_entity("p4", "pr", "Add refresh lock to auth module",
                 "Implements the lock discussed in i9.", "u/p4")
    s.add_entity("c2", "commit", "Replace refresh lock with queue",
                 "The lock caused deadlocks under load; queue instead.", "u/c2")
    s.add_edge("c1", "i9", "fixes")
    s.add_edge("p4", "c1", "references")
    s.add_edge("c1", "c2", "supersedes")
    return s


class TestGraph(unittest.TestCase):
    def test_add_and_find(self):
        s = demo_store()
        ranked = s.find_by_tokens(["token", "expiry"])
        self.assertTrue(ranked)
        self.assertEqual(ranked[0][1]["id"], "c1")

    def test_neighbors(self):
        s = demo_store()
        nbs = s.neighbors("c1")
        self.assertEqual({n["id"] for n in nbs}, {"i9", "c2"})


class TestQA(unittest.TestCase):
    def test_finds_evidence(self):
        r = ask(demo_store(), "why does the auth refresh use a lock?")
        self.assertFalse(r["refused"])
        self.assertTrue(r["evidence"])
        self.assertGreater(r["confidence"], 0)

    def test_refuses_unknown(self):
        r = ask(demo_store(), "why does the payment gateway use stripes?")
        self.assertTrue(r["refused"])

    def test_refuses_when_a_term_is_absent_from_graph(self):
        # "microservices" appears in no ingested record, so the question
        # is refused even though generic words like "auth" match.
        r = ask(demo_store(), "why auth microservices?")
        self.assertTrue(r["refused"])

    def test_supersession_noted(self):
        r = ask(demo_store(), "why token expiry race fix in auth refresh?")
        self.assertIn("superseded", r["answer"])

    def test_title_match_breaks_token_tie(self):
        # Both records match 2/2 tokens, but only one has them in its
        # title; the title record must win over the passing mention.
        s = GraphStore()
        s.add_entity("t1", "issue", "Python compatibility notes", "", "u/t1")
        s.add_entity("t2", "doc", "Mailers factory",
                     "python compatibility mentioned in passing", "u/t2")
        s.add_entity("x", "file", "notes.py", "", "u/x")
        s.add_edge("t1", "x", "references")
        r = ask(s, "why python compatibility?")
        self.assertFalse(r["refused"])
        self.assertEqual(r["match"]["id"], "t1")

    def test_chain_size_breaks_remaining_tie(self):
        # Same matched count, same title hits: richer chain wins.
        s = GraphStore()
        s.add_entity("t3", "issue", "Python compatibility A", "", "u/t3")
        s.add_entity("t4", "issue", "Python compatibility B", "", "u/t4")
        s.add_entity("x", "file", "a.py", "", "u/x")
        s.add_entity("y", "file", "b.py", "", "u/y")
        s.add_entity("z", "file", "c.py", "", "u/z")
        s.add_edge("t3", "x", "references")
        s.add_edge("t4", "y", "references")
        s.add_edge("t4", "z", "references")
        r = ask(s, "why python compatibility?")
        self.assertFalse(r["refused"])
        self.assertEqual(r["match"]["id"], "t4")

    def test_refuses_when_best_match_has_no_evidence_chain(self):
        # A passing mention with zero linked records is not an answer,
        # even at full token confidence.
        s = GraphStore()
        s.add_entity("t2", "doc", "Mailers factory",
                     "python compatibility mentioned in passing", "u/t2")
        r = ask(s, "why python compatibility?")
        self.assertTrue(r["refused"])
        self.assertIn("no evidence chain", r["reason"])


if __name__ == "__main__":
    unittest.main()
