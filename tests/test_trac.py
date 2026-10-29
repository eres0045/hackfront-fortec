"""Tests for Trac ticket parsing (fixture HTML, no network)."""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from whycode.trac import parse_ticket_html

FIXTURE = """
<html><head><title>
      #37089 (ignore_warnings() handles message arg differently)
          \u2013 Django
    </title></head><body>
<div class="description"><h3>Description</h3>
<div class="searchable"><p>ignore_warnings treats its message argument
inconsistently with the other test helpers.</p></div></div>
<div class="comment searchable"><p>Agreed, matching substrings by default
seems right.</p></div>
</body></html>
"""


class TestTracParse(unittest.TestCase):
    def test_title_and_body(self):
        p = parse_ticket_html(FIXTURE)
        self.assertIn("ignore_warnings", p["title"])
        self.assertIn("inconsistently", p["body"])
        self.assertIn("matching substrings", p["body"])


if __name__ == "__main__":
    unittest.main()
