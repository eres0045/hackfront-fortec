# -*- coding: utf-8 -*-
"""WhyCode Security & Privacy Engine (Open-Source Standards).

Implements proven, battle-tested privacy and security protections adapted from:
1. Gitleaks (zricethezav/gitleaks) - Pattern-based credential & API key detection.
2. Yelp detect-secrets (Yelp/detect-secrets) - Shannon entropy calculation for high-entropy tokens.
3. Microsoft Presidio (microsoft/presidio) - Regex-based PII redaction (emails, IPs).
4. OWASP Subprocess Security - Command injection & git flag injection mitigation.
"""

import math
import os
import re
from typing import Dict, List, Optional, Tuple


# ==============================================================================
# 1. GITLEAKS-DERIVED SECRET DETECTION PATTERNS
# ==============================================================================

GITLEAKS_PATTERNS: List[Tuple[str, re.Pattern]] = [
    ("AWS_KEY", re.compile(r'\b(AKIA[0-9A-Z]{16})\b')),
    ("AWS_SECRET", re.compile(r'(?i)aws_secret_access_key\s*[:=]\s*["\']?([a-zA-Z0-9/+=]{40})["\']?')),
    ("GITHUB_PAT", re.compile(r'\b(ghp_[a-zA-Z0-9]{36}|github_pat_[a-zA-Z0-9_]{82})\b')),
    ("GITHUB_OAUTH", re.compile(r'\b(gho_[a-zA-Z0-9]{36})\b')),
    ("OPENAI_KEY", re.compile(r'\b(sk-[a-zA-Z0-9]{48}|sk-proj-[a-zA-Z0-9_\-]{48,})\b')),
    ("ANTHROPIC_KEY", re.compile(r'\b(sk-ant-[a-zA-Z0-9_\-]{32,})\b')),
    ("SLACK_WEBHOOK", re.compile(r'https://hooks\.slack\.com/services/T[0-9A-Z]{8}/B[0-9A-Z]{8}/[0-9a-zA-Z]{24}')),
    ("STRIPE_KEY", re.compile(r'\b(sk_live_[0-9a-zA-Z]{24})\b')),
    ("JWT_TOKEN", re.compile(r'\beyJ[a-zA-Z0-9_\-]{10,}\.eyJ[a-zA-Z0-9_\-]{10,}\.[a-zA-Z0-9_\-]{10,}\b')),
    ("PRIVATE_KEY", re.compile(r'-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----[^-]+-----END (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----', re.DOTALL)),
    ("GENERIC_SECRET", re.compile(r'(?i)(?:api_?key|access_token|secret_?key|client_secret|auth_token)\s*[:=]\s*["\']([a-zA-Z0-9_\-\.]{16,64})["\']')),
]


# ==============================================================================
# 2. YELP DETECT-SECRETS SHANNON ENTROPY DETECTOR
# ==============================================================================

def calculate_shannon_entropy(data: str) -> float:
    """Computes Shannon entropy H = -sum(p * log2(p)).
    
    High entropy (typically > 4.2 for Base64, > 3.0 for Hex) indicates
    cryptographic keys or random tokens rather than natural language.
    """
    if not data:
        return 0.0
    entropy = 0.0
    length = len(data)
    frequencies = {}
    for char in data:
        frequencies[char] = frequencies.get(char, 0) + 1
    for count in frequencies.values():
        p = count / length
        entropy -= p * math.log2(p)
    return entropy


# ==============================================================================
# 3. PII REDACTION (PRESIDIO COMPATIBLE)
# ==============================================================================

EMAIL_REGEX = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b')
IPV4_REGEX = re.compile(r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b')


def redact_pii(text: str, mask_emails: bool = True, mask_ips: bool = True) -> Tuple[str, int]:
    """Redacts developer email addresses and IP addresses."""
    redaction_count = 0
    result = text

    if mask_emails:
        emails = EMAIL_REGEX.findall(result)
        if emails:
            redaction_count += len(emails)
            result = EMAIL_REGEX.sub("[REDACTED_EMAIL]", result)

    if mask_ips:
        ips = IPV4_REGEX.findall(result)
        if ips:
            # Exclude common loopbacks from aggressive redaction
            valid_ips = [ip for ip in ips if ip not in ("127.0.0.1", "0.0.0.0")]
            if valid_ips:
                redaction_count += len(valid_ips)
                for ip in valid_ips:
                    result = result.replace(ip, "[REDACTED_IP]")

    return result, redaction_count


# ==============================================================================
# 4. MASTER SECRET & METADATA SCRUBBER
# ==============================================================================

def scrub_text(
    text: str,
    redact_secrets: bool = True,
    redact_pii_enabled: bool = True,
    check_entropy: bool = True
) -> Tuple[str, Dict[str, int]]:
    """Scrubs sensitive information from commit logs, PRs, and diff metadata.
    
    Returns:
        (sanitized_text, audit_counts)
    """
    if not text:
        return text, {}

    counts: Dict[str, int] = {
        "secrets_redacted": 0,
        "pii_redacted": 0,
        "entropy_flags": 0,
    }
    sanitized = text

    # Step 1: Gitleaks Pattern Matching
    if redact_secrets:
        for rule_id, pattern in GITLEAKS_PATTERNS:
            matches = list(pattern.finditer(sanitized))
            if matches:
                counts["secrets_redacted"] += len(matches)
                sanitized = pattern.sub(f"[REDACTED_{rule_id}]", sanitized)

    # Step 2: High-Entropy Word Scanning (Detect-Secrets)
    if check_entropy:
        words = sanitized.split()
        high_entropy_words = []
        for word in words:
            clean_word = word.strip('"\'`:,;()[]{}')
            if len(clean_word) >= 20 and not clean_word.startswith("[REDACTED_"):
                # Only check strings that look like keys/hashes (alphanumeric/b64)
                if re.match(r'^[A-Za-z0-9+/=_\-]+$', clean_word):
                    entropy = calculate_shannon_entropy(clean_word)
                    if entropy >= 4.3:  # Proven threshold from Yelp detect-secrets
                        high_entropy_words.append(clean_word)

        if high_entropy_words:
            counts["entropy_flags"] += len(high_entropy_words)
            for bad in high_entropy_words:
                sanitized = sanitized.replace(bad, "[REDACTED_HIGH_ENTROPY_TOKEN]")

    # Step 3: PII Redaction
    if redact_pii_enabled:
        sanitized, pii_count = redact_pii(sanitized)
        counts["pii_redacted"] = pii_count

    return sanitized, counts


# ==============================================================================
# 5. SUBPROCESS & GIT COMMAND INJECTION SHIELD
# ==============================================================================

def validate_repo_path_or_url(target: str) -> Tuple[bool, str]:
    """Validates repository input to prevent command/flag injection.
    
    Prevents attacks like:
        --upload-pack=malicious_cmd
        -u /path/to/evil
    """
    target = target.strip()
    if not target:
        return False, "Empty repository target"

    # Flag injection defense: never allow arguments beginning with '-'
    if target.startswith("-"):
        return False, "Invalid repository: arguments starting with '-' are prohibited"

    # URL validation
    if target.startswith("http://") or target.startswith("https://"):
        # Match standard GitHub / GitLab URL formats
        url_pattern = re.compile(r'^https?://[a-zA-Z0-9\-.]+(?::[0-9]+)?/[a-zA-Z0-9_\-./]+(?:\.git)?$')
        if not url_pattern.match(target):
            return False, "Invalid repository URL format"
        return True, "Valid URL"

    # Local Directory validation
    if os.path.exists(target):
        return True, "Valid local directory"

    # Standard owner/repo shorthand (e.g. 'psf/requests' or 'django/django')
    shorthand_pattern = re.compile(r'^[a-zA-Z0-9_\-\.]+/[a-zA-Z0-9_\-\.]+$')
    if shorthand_pattern.match(target):
        return True, "Valid repository shorthand"

    return False, "Target is neither an existing directory nor a valid repository URL"
