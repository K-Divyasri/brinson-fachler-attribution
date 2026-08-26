import pytest

from attribution.risk import component_risk_attribution


def test_two_sector_hand_computed():
    # equal weights, no correlation: variance is just the weighted average
    # of individual variances, easy to check by hand.
    weights = {"A": 0.5, "B": 0.5}
    covariance = {
        "A": {"A": 0.04, "B": 0.0},
        "B": {"A": 0.0, "B": 0.09},
    }
    # portfolio variance = 0.5^2*0.04 + 0.5^2*0.09 = 0.01 + 0.0225 = 0.0325
    result = component_risk_attribution(weights, covariance)
    assert result.portfolio_volatility == pytest.approx(0.0325**0.5)
    assert result.reconciliation_error() == pytest.approx(0.0, abs=1e-12)

    sector_b = next(s for s in result.sectors if s.sector == "B")
    # B has the bigger variance and equal weight -> bigger risk share
    sector_a = next(s for s in result.sectors if s.sector == "A")
    assert sector_b.component_contribution > sector_a.component_contribution
    assert sector_b.pct_of_risk + sector_a.pct_of_risk == pytest.approx(1.0)


def test_single_sector_all_risk_is_its_own():
    weights = {"Only": 1.0}
    covariance = {"Only": {"Only": 0.05}}
    result = component_risk_attribution(weights, covariance)
    assert result.sectors[0].pct_of_risk == pytest.approx(1.0)
    assert result.sectors[0].component_contribution == pytest.approx(result.portfolio_volatility)


def test_reconciles_on_realistic_multi_sector_book():
    from attribution.data import BENCHMARK_WEIGHTS, generate_sector_covariance

    cov = generate_sector_covariance()
    result = component_risk_attribution(BENCHMARK_WEIGHTS, cov)
    assert result.reconciliation_error() == pytest.approx(0.0, abs=1e-9)
    assert result.portfolio_volatility > 0


def test_mismatched_sectors_raise():
    with pytest.raises(ValueError, match="square"):
        component_risk_attribution({"A": 1.0}, {"B": {"B": 0.01}})
