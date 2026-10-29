"""Fixture-based tests for ingestion linking (no network)."""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from whycode.graph import GraphStore
from whycode.ingest import link_refs


class TestLinking(unittest.TestCase):
    def test_fixes_and_references(self):
        s = GraphStore()
        s.add_entity("issue:5", "issue", "Crash on empty form")
        s.add_entity("pr:9", "pr", "Fix crash")
        number_to_id = {"5": "issue:5", "9": "pr:9"}
        link_refs(s, "commit:abc", "Fixes #5, see also #9", number_to_id)
        edges = {(e["relation"], e["id"])
                 for e in s.neighbors("commit:abc")}
        self.assertIn(("fixes", "issue:5"), edges)
        self.assertNotIn(("references", "issue:5"), edges)
        self.assertIn(("references", "pr:9"), edges)

    def test_fixed_past_tense_counts_as_fix(self):
        # Django's convention is "Fixed #N", not "Fixes #N".
        s = GraphStore()
        s.add_entity("issue:7", "issue", "Some ticket")
        link_refs(s, "commit:xyz", "Fixed #7 -- Did the thing.",
                  {"7": "issue:7"})
        edges = {(e["relation"], e["id"])
                 for e in s.neighbors("commit:xyz")}
        self.assertIn(("fixes", "issue:7"), edges)

    def test_unknown_numbers_ignored(self):
        s = GraphStore()
        link_refs(s, "commit:abc", "See #99999", {})
        self.assertEqual(s.neighbors("commit:abc"), [])


if __name__ == "__main__":
    unittest.main()
