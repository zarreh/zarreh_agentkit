"""Deterministic prompt-injection screening by named rule.

Two services each shipped a regex layer under their LLM-based injection check:
one a single pattern returning a bool, the other a dict of named patterns
returning the first rule hit. This is the named-rule form, with the union of
both catalogues. It favours recall: the deterministic layer is the cheap,
auditable first gate, and a false positive costs a refusal, not a leak.
"""

from __future__ import annotations

import re
from collections.abc import Mapping

INJECTION_PATTERNS: Mapping[str, re.Pattern[str]] = {
    "ignore-instructions": re.compile(
        r"\bignore\s+(all\s+|any\s+)?(the\s+)?(previous|prior|above)\s+instructions?\b",
        re.IGNORECASE,
    ),
    "disregard-rules": re.compile(
        r"\bdisregard\s+(your\s+|the\s+|all\s+)?"
        r"(rules|instructions|guidelines|policy|above|prior|previous)\b",
        re.IGNORECASE,
    ),
    "reveal-system-prompt": re.compile(
        r"\b(reveal|show|print|repeat)\s+(your\s+|the\s+)?(system\s+prompt|instructions|prompt)\b",
        re.IGNORECASE,
    ),
    "role-override": re.compile(
        r"\byou\s+are\s+now\b|\bact\s+as\s+(a|an|if|though)\b|\bpretend\s+(you\s+are|to\s+be)\b",
        re.IGNORECASE,
    ),
    "developer-mode": re.compile(r"\bdeveloper\s+mode\b|\bjailbreak\b", re.IGNORECASE),
    "injected-role-marker": re.compile(r"\bsystem\s*:|\bnew\s+instructions?\s*:", re.IGNORECASE),
}


def first_matching_rule(
    text: str, patterns: Mapping[str, re.Pattern[str]] = INJECTION_PATTERNS
) -> str | None:
    """The name of the first pattern (in mapping order) that matches `text`."""
    for rule_id, pattern in patterns.items():
        if pattern.search(text):
            return rule_id
    return None
