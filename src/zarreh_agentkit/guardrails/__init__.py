"""Guardrail primitives shared across agent services.

Each primitive here was independently reimplemented in at least two
consuming services before being promoted — the same extraction rule the
rest of the package follows. What's shared is the mechanism; the
domain-specific policy (what happens on breach, which fields a given tool
may return) stays in each consumer.
"""

from zarreh_agentkit.guardrails.budget import Budget, budget_breach_reason, count_tool_calls
from zarreh_agentkit.guardrails.grounding import (
    ClaimJudgmentLike,
    count_unsupported,
    grounding_confidence,
    unsupported_claims_feedback,
)
from zarreh_agentkit.guardrails.injection import INJECTION_PATTERNS, first_matching_rule
from zarreh_agentkit.guardrails.projection import project_fields

__all__ = [
    "INJECTION_PATTERNS",
    "Budget",
    "ClaimJudgmentLike",
    "budget_breach_reason",
    "count_tool_calls",
    "count_unsupported",
    "first_matching_rule",
    "grounding_confidence",
    "project_fields",
    "unsupported_claims_feedback",
]
