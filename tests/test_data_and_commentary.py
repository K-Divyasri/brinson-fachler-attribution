from attribution.brinson_fachler import brinson_fachler
from attribution.commentary import linked_note, risk_note, single_period_note
from attribution.data import (
    BENCHMARK_WEIGHTS,
    PORTFOLIO_WEIGHTS,
    generate_monthly_periods,
    generate_sector_covariance,
)
from attribution.linking import link_periods
from attribution.risk import component_risk_attribution


def test_generate_monthly_periods_shape_and_determinism():
    periods_a = generate_monthly_periods(n_months=6, seed=1)
    periods_b = generate_monthly_periods(n_months=6, seed=1)
    assert len(periods_a) == 6
    assert periods_a[0].portfolio_returns == periods_b[0].portfolio_returns
    assert set(periods_a[0].portfolio_returns) == set(BENCHMARK_WEIGHTS)


def test_generate_monthly_periods_different_seed_differs():
    a = generate_monthly_periods(n_months=6, seed=1)
    b = generate_monthly_periods(n_months=6, seed=2)
    assert a[0].portfolio_returns != b[0].portfolio_returns


def test_energy_and_financials_have_positive_average_selection():
    """The demo dataset bakes in positive selection alpha for Energy and
    Financials (data.SELECTION_ALPHA_BPS) -- confirm the generated data
    actually reflects that bias on average, not just that the constant
    exists unused."""
    periods = generate_monthly_periods(n_months=24, seed=7)
    for sector in ("Energy", "Financials"):
        diffs = [p.portfolio_returns[sector] - p.benchmark_returns[sector] for p in periods]
        assert sum(diffs) / len(diffs) > 0


def test_commentary_functions_run_on_real_results():
    periods = generate_monthly_periods(n_months=12, seed=7)
    single = brinson_fachler(
        PORTFOLIO_WEIGHTS, BENCHMARK_WEIGHTS, periods[0].portfolio_returns, periods[0].benchmark_returns
    )
    linked = link_periods(periods, PORTFOLIO_WEIGHTS, BENCHMARK_WEIGHTS)
    risk = component_risk_attribution(BENCHMARK_WEIGHTS, generate_sector_covariance())

    assert "Portfolio returned" in single_period_note(single)
    assert "Carino-linked" in linked_note(linked)
    assert "volatility" in risk_note(risk)
