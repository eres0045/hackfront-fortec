"""Unit and integration test suite for WhyCode MCP Server tools."""
import unittest
import os
import json

from whycode.mcp_server import (
    whycode_ask,
    whycode_list_repos,
    whycode_telemetry,
    whycode_get_entity
)

class TestWhyCodeMCP(unittest.TestCase):
    def test_whycode_list_repos(self):
        repos = whycode_list_repos()
        self.assertIsInstance(repos, list)
        self.assertTrue(len(repos) >= 2)
        repo_names = [r["repo"] for r in repos]
        self.assertIn("django/django", repo_names)
        self.assertIn("psf/requests", repo_names)
        print("✓ whycode_list_repos tested successfully!")

    def test_whycode_telemetry(self):
        telemetry = whycode_telemetry()
        self.assertIn("system_1", telemetry)
        self.assertIn("system_2", telemetry)
        self.assertEqual(telemetry["system_1"]["latency"], "12.0 microseconds")
        print("✓ whycode_telemetry tested successfully!")

    def test_whycode_ask_valid(self):
        # Query that exists in whycode.db
        res = whycode_ask(
            question="why did Django avoid duplicate joins in filter after aggregation?",
            repo="django/django"
        )
        self.assertIn("WhyCode Architectural Decision Rationale", res)
        self.assertIn("pr:22207", res)
        self.assertIn("EXISTS", res)
        self.assertIn("Grounded Evidence Chain", res)
        print("✓ whycode_ask (grounded hit) tested successfully!")

    def test_whycode_ask_refusal(self):
        # Query with ungrounded term that triggers Conformal Gate abstention
        res = whycode_ask(
            question="why does Django use quantum blockchain microservices?",
            repo="django/django"
        )
        self.assertIn("Conformal Gate: Abstention", res)
        self.assertIn("Refused", res)
        print("✓ whycode_ask (conformal refusal) tested successfully!")

    def test_whycode_get_entity(self):
        res = whycode_get_entity("pr:22207", repo="django/django")
        self.assertTrue(res["found"])
        self.assertEqual(res["entity"]["id"], "pr:22207")
        self.assertIn("relations", res)
        print("✓ whycode_get_entity tested successfully!")

if __name__ == "__main__":
    unittest.main()
