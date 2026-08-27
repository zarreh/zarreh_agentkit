"""Least-privilege field projection — the "narrow view" convention.

Every node/tool in a graph should see and return only the fields its
specific purpose needs, even among data that has already cleared a coarser
privacy boundary (de-identification, redaction). A field that was never
serialised into a tool's output cannot leak regardless of what the model is
told or asked; a prompt instruction to "only mention relevant fields" can be
talked out of by an adversarial or confused conversation.

The allowlist itself (which fields a given tool/view may return) is
domain-specific and stays with the consumer; this module owns only the
mechanism that enforces it.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


def project_fields(record: BaseModel, allowed_fields: frozenset[str]) -> dict[str, Any]:
    """Serialises `record` to a dict containing only `allowed_fields`.

    Fields not in the allowlist are dropped, never passed through by
    default — a caller must say what a view may return before it can
    return anything.
    """
    full = record.model_dump(mode="json")
    return {key: value for key, value in full.items() if key in allowed_fields}
