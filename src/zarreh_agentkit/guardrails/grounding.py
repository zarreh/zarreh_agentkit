"""Aggregate per-claim grounding judgments into a verdict and retry feedback.

Two services independently built a "judge each extracted claim against the
evidence, then loop back with feedback if any is unsupported" step with the
same confidence ladder, the same unsupported count and the same feedback
message shape. What is shared is that aggregation. The claim and judgment
schemas stay app-specific: they are LLM structured-output schemas bound to
each app's prompts and evidence model.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Literal, Protocol

Confidence = Literal["high", "medium", "low"]


class ClaimJudgmentLike(Protocol):
    @property
    def claim_id(self) -> str: ...

    @property
    def supported(self) -> bool: ...

    @property
    def reason(self) -> str: ...


def count_unsupported(judgments: Iterable[ClaimJudgmentLike]) -> int:
    return sum(1 for j in judgments if not j.supported)


def grounding_confidence(unsupported: int) -> Confidence:
    """`high` with every claim supported, `medium` with one gap, else `low`."""
    if unsupported == 0:
        return "high"
    if unsupported == 1:
        return "medium"
    return "low"


def unsupported_claims_feedback(
    judgments: Iterable[ClaimJudgmentLike],
    header: str,
    claim_text_by_id: Mapping[str, str] | None = None,
) -> str:
    """`header` followed by one `- "<claim>" — <reason>` line per unsupported
    claim; the claim is shown by its text when `claim_text_by_id` has it, else
    by id. Fed back to the drafting step as a retry instruction."""
    labels = claim_text_by_id or {}
    lines = [
        f'- "{labels.get(j.claim_id, j.claim_id)}" — {j.reason}'
        for j in judgments
        if not j.supported
    ]
    return header + "\n" + "\n".join(lines)
