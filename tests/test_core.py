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


if __name__ == "__main__":
    unittest.main()
