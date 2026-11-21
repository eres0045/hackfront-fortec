# -*- coding: utf-8 -*-
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from whycode.security import (
    calculate_shannon_entropy,
    redact_pii,
    scrub_text,
    validate_repo_path_or_url
)

class TestSecurity(unittest.TestCase):
    def test_gitleaks_pattern_redaction(self):
        text = "Deploy token ghp_111122223333444455556666777788889999 and aws AKIA1234567890ABCDEF"
        sanitized, counts = scrub_text(text)
        self.assertNotIn("ghp_111122223333444455556666777788889999", sanitized)
        self.assertNotIn("AKIA1234567890ABCDEF", sanitized)
        self.assertIn("[REDACTED_GITHUB_PAT]", sanitized)
        self.assertIn("[REDACTED_AWS_KEY]", sanitized)
        self.assertGreaterEqual(counts.get("secrets_redacted", 0), 2)

    def test_pii_email_redaction(self):
        text = "Committed by developer Jane Doe <jane.doe@enterprise.corp>"
        sanitized, counts = scrub_text(text)
        self.assertNotIn("jane.doe@enterprise.corp", sanitized)
        self.assertIn("[REDACTED_EMAIL]", sanitized)
        self.assertGreaterEqual(counts.get("pii_redacted", 0), 1)

    def test_shannon_entropy(self):
        low_entropy = "aaaaabbbbbccccc"
        high_entropy = "dGhpcy1pcy1hLXZlcnktcmFuZG9tLXRva2VuLTEyMzQ1Ng=="
        self.assertLess(calculate_shannon_entropy(low_entropy), 2.5)
        self.assertGreater(calculate_shannon_entropy(high_entropy), 4.2)

    def test_flag_injection_prevention(self):
        valid, msg = validate_repo_path_or_url("--upload-pack=exploit")
        self.assertFalse(valid)
        self.assertIn("prohibited", msg)

        valid_url, _ = validate_repo_path_or_url("https://github.com/django/django")
        self.assertTrue(valid_url)

if __name__ == "__main__":
    unittest.main()
