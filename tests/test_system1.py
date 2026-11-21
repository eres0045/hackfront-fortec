"""Unit tests for WhyCode System 1 Decision Engine."""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from whycode.graph import GraphStore
from whycode.qa import ask
from whycode.system1 import System1Engine, Intent


def sample_store():
    s = GraphStore()
    s.add_entity("c1", "commit", "Fixed #100 -- Add async routing support",
                 "Adds async support to url dispatcher.", "u/c1")
    s.add_entity("dep9", "doc", "DEP 0009: Async-capable Django",
                 "Discusses async support and rejected options like forking.", "u/dep9")
    s.add_entity("f1", "file", "django/urls/resolvers.py", "", "u/f1")
    s.add_edge("c1", "dep9", "references")
    s.add_edge("dep9", "f1", "mentions")
    return s


class TestSystem1Engine(unittest.TestCase):
    def setUp(self):
        self.engine = System1Engine(abstain_threshold=0.35)
        self.store = sample_store()

    def test_classify_why_decision(self):
        intent = self.engine.classify_intent("Why does Django use async routing?")
        self.assertEqual(intent, Intent.WHY_DECISION)

    def test_classify_why_not(self):
        intent = self.engine.classify_intent("Why didn't Django fork instead of adding async?")
        self.assertEqual(intent, Intent.WHY_NOT)

    def test_classify_superseded(self):
        intent = self.engine.classify_intent("Why was the old routing superseded by DEP 9?")
        self.assertEqual(intent, Intent.SUPERSEDED)

    def test_abstention_on_ungrounded_token(self):
        decision = self.engine.decide(self.store, "Why does Django use quasiflobber?")
        self.assertTrue(decision.abstain)
        self.assertIn("quasiflobber", decision.abstain_reason)

    def test_pass_on_grounded_query(self):
        decision = self.engine.decide(self.store, "Why async routing support?")
        self.assertFalse(decision.abstain)
        self.assertGreater(decision.confidence, 0.35)

    def test_qa_integration_system1_metadata(self):
        result = ask(self.store, "Why didn't Django fork instead of adding async?")
        self.assertIn("system1", result)
        self.assertEqual(result["system1"]["intent"], "why_not")
        self.assertTrue(result["system1"]["is_negative"])


if __name__ == "__main__":
    unittest.main()
