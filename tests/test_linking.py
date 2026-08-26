import random

import pytest

from attribution.data import Period
from attribution.linking import _carino_factor, _geometric_cumulative, link_periods


def test_carino_factor_limit_when_returns_equal():
    # when rp == rb, the factor is the L'Hopital limit 1/(1+rb), not a
    # division-by-zero crash
    factor = _carino_factor(0.05, 0.05)
    assert factor == pytest.approx(1 / 1.05)


def test_geometric_cumulative_matches_manual_compounding():
    returns = [0.02, -0.01, 0.03]
    expected = (1.02 * 0.99 * 1.03) - 1
    assert _geometric_cumulative(returns) == pytest.approx(expected)


def _make_random_periods(n_periods: int, seed: int) -> tuple[list[Period], dict, dict]:
    rng = random.Random(seed)
    sectors = [f"S{i}" for i in range(5)]
    raw_wp = [rng.uniform(1, 10) for _ in sectors]
    raw_wb = [rng.uniform(1, 10) for _ in sectors]
    wp = {s: w / sum(raw_wp) for s, w in zip(sectors, raw_wp)}
    wb = {s: w / sum(raw_wb) for s, w in zip(sectors, raw_wb)}

    periods = []
    for t in range(n_periods):
        rb = {s: rng.gauss(0.008, 0.04) for s in sectors}
        rp = {s: rb[s] + rng.gauss(0.0, 0.01) for s in sectors}
        periods.append(Period(label=f"P{t}", benchmark_returns=rb, portfolio_returns=rp))
    return periods, wp, wb


def test_linked_result_reconciles_to_cumulative_active_return():
    periods, wp, wb = _make_random_periods(n_periods=12, seed=1)
    result = link_periods(periods, wp, wb)
    assert result.reconciliation_error() == pytest.approx(0.0, abs=1e-9)


def test_linked_result_reconciles_with_single_period():
    """A one-period 'link' should reduce to the plain single-period
    attribution -- k_t/K == 1 when there's only one period."""
    periods, wp, wb = _make_random_periods(n_periods=1, seed=2)
    result = link_periods(periods, wp, wb)
    assert result.reconciliation_error() == pytest.approx(0.0, abs=1e-9)
    assert result.cumulative_active_return == pytest.approx(
        result.period_results[0].active_return, abs=1e-9
    )


def test_empty_periods_raises():
    with pytest.raises(ValueError, match="at least one period"):
        link_periods([], {"A": 1.0}, {"A": 1.0})


def test_naive_sum_would_have_drifted():
    """Demonstrates WHY linking is needed: summing each period's raw
    (unlinked) total effect across many periods does NOT equal the
    cumulative geometric active return once returns are large enough for
    compounding to matter. This is the negative control for the positive
    reconciliation test above."""
    periods, wp, wb = _make_random_periods(n_periods=24, seed=3)
    linked = link_periods(periods, wp, wb)

    naive_sum = sum(s.total for r in linked.period_results for s in r.sectors)
    assert naive_sum != pytest.approx(linked.cumulative_active_return, abs=1e-6)
