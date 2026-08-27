"""Canonical-scenario eval runner shell, shared across agent services.

The CLI shell — run a suite, print a pass/fail matrix, exit non-zero on any
mismatch so it gates CI — was identical in shape across services; the
metrics that decide pass/fail are not. This module owns the shell only.
"""

from zarreh_agentkit.evals.runner import EvalOutcome, run_eval_cli

__all__ = [
    "EvalOutcome",
    "run_eval_cli",
]
