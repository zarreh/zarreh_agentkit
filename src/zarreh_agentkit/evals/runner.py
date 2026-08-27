"""The `make eval` shell: run a suite, print it, gate on any failure.

Each service defines its own scenario shape, its own metrics, and its own
printer — those don't generalise (HARVEST: "the runner is shareable, the
metric set is not"). What generalises is the three-step shell around them:
run the suite once, print whatever report the service wants, then fail the
process if any case didn't meet its expected outcome. Kept decoupled from
the print step deliberately, so a service's existing rich matrix printer
(expected vs. actual columns, cost, latency, ...) keeps working unchanged —
`outcomes` only needs to say which cases passed.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class EvalOutcome:
    """One canonical case's pass/fail, independent of how it's printed."""

    case_id: str
    passed: bool


def run_eval_cli[ResultsT](
    run_suite: Callable[[], ResultsT],
    print_report: Callable[[ResultsT], None],
    outcomes: Callable[[ResultsT], Sequence[EvalOutcome]],
) -> int:
    """Run `run_suite`, print its report, and return the CI exit code.

    `run_suite` executes every canonical case and returns whatever
    app-specific results object `print_report` and `outcomes` both know how
    to read. Returns 1 if any case's `EvalOutcome.passed` is False, 0
    otherwise — the same gate every existing consumer already implements by
    hand.
    """
    results = run_suite()
    print_report(results)
    failures = [o for o in outcomes(results) if not o.passed]
    if failures:
        names = ", ".join(o.case_id for o in failures)
        print(
            f"\n{len(failures)} canonical scenario(s) did not match their expected outcome: {names}"
        )
        return 1
    print("\nAll canonical scenarios matched their expected outcome.")
    return 0
