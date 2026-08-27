from dataclasses import dataclass

from zarreh_agentkit.evals.runner import EvalOutcome, run_eval_cli


@dataclass
class FakeResults:
    rows: list[tuple[str, bool]]


def test_all_passing_returns_zero(capsys) -> None:  # type: ignore[no-untyped-def]
    results = FakeResults(rows=[("c1", True), ("c2", True)])
    exit_code = run_eval_cli(
        run_suite=lambda: results,
        print_report=lambda r: print(f"n={len(r.rows)}"),
        outcomes=lambda r: [EvalOutcome(case_id=cid, passed=ok) for cid, ok in r.rows],
    )
    assert exit_code == 0
    assert "All canonical scenarios matched" in capsys.readouterr().out


def test_any_failure_returns_one_and_names_it(capsys) -> None:  # type: ignore[no-untyped-def]
    results = FakeResults(rows=[("c1", True), ("c2", False)])
    exit_code = run_eval_cli(
        run_suite=lambda: results,
        print_report=lambda r: None,
        outcomes=lambda r: [EvalOutcome(case_id=cid, passed=ok) for cid, ok in r.rows],
    )
    out = capsys.readouterr().out
    assert exit_code == 1
    assert "1 canonical scenario(s)" in out
    assert "c2" in out


def test_run_suite_called_exactly_once() -> None:
    calls = {"n": 0}

    def run_suite() -> FakeResults:
        calls["n"] += 1
        return FakeResults(rows=[("c1", True)])

    run_eval_cli(
        run_suite=run_suite,
        print_report=lambda r: None,
        outcomes=lambda r: [EvalOutcome(case_id=cid, passed=ok) for cid, ok in r.rows],
    )
    assert calls["n"] == 1
