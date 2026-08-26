"""Synthetic sector-level portfolio and benchmark data.

Illustrative, not live market data. Weights are set close to real S&P 500
GICS sector weights (2024-era, rounded) so the numbers feel plausible; a
handful of deliberate over/underweights and a deliberate stock-selection
skill pattern are baked in so the attribution has a clear story to tell,
the same way project 07's synthetic prices are shaped to make a VaR model
fail or a FHS model pass on purpose.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

SECTORS = [
    "Information Technology",
    "Financials",
    "Health Care",
    "Consumer Discretionary",
    "Communication Services",
    "Industrials",
    "Consumer Staples",
    "Energy",
    "Utilities",
    "Materials",
]

# Approximate benchmark (S&P 500-like) sector weights, sums to 1.0.
BENCHMARK_WEIGHTS: dict[str, float] = {
    "Information Technology": 0.30,
    "Financials": 0.13,
    "Health Care": 0.12,
    "Consumer Discretionary": 0.10,
    "Communication Services": 0.09,
    "Industrials": 0.08,
    "Consumer Staples": 0.06,
    "Energy": 0.04,
    "Utilities": 0.03,
    "Materials": 0.05,
}

# Portfolio weights: overweight Tech and Energy (a bet that pays off),
# underweight Utilities and Consumer Staples (defensive sectors sat out).
PORTFOLIO_WEIGHTS: dict[str, float] = {
    "Information Technology": 0.38,
    "Financials": 0.13,
    "Health Care": 0.11,
    "Consumer Discretionary": 0.09,
    "Communication Services": 0.08,
    "Industrials": 0.07,
    "Consumer Staples": 0.02,
    "Energy": 0.08,
    "Utilities": 0.01,
    "Materials": 0.03,
}

# Per-sector monthly selection alpha baked into the portfolio's own return
# on top of the benchmark sector return -- positive means good stock
# picking within that sector, negative means poor picking. Financials and
# Energy are the deliberate "good picker" sectors; Real-Estate-adjacent
# Materials is the deliberate "poor picker" sector. Left at 0 elsewhere so
# most of the story comes from allocation, not selection.
SELECTION_ALPHA_BPS: dict[str, float] = {
    "Information Technology": 0.0005,
    "Financials": 0.006,
    "Health Care": 0.0,
    "Consumer Discretionary": 0.0,
    "Communication Services": 0.0,
    "Industrials": 0.0,
    "Consumer Staples": 0.0,
    "Energy": 0.008,
    "Utilities": 0.0,
    "Materials": -0.006,
}

assert abs(sum(BENCHMARK_WEIGHTS.values()) - 1.0) < 1e-9
assert abs(sum(PORTFOLIO_WEIGHTS.values()) - 1.0) < 1e-9
assert set(BENCHMARK_WEIGHTS) == set(PORTFOLIO_WEIGHTS) == set(SECTORS)


@dataclass
class Period:
    label: str
    benchmark_returns: dict[str, float]
    portfolio_returns: dict[str, float]


def generate_monthly_periods(n_months: int = 12, seed: int = 7) -> list[Period]:
    """Generate `n_months` of sector returns for both books. Each sector's
    monthly benchmark return is a shared random draw (with sector-specific
    drift/vol so Tech is more volatile than Utilities, roughly matching
    reality); the portfolio's return in that same sector equals the
    benchmark's return plus the sector's fixed selection alpha plus a
    little independent noise -- weights themselves are held constant
    across months (a static, buy-and-hold allocation), which keeps the
    Brinson-Fachler story about allocation vs. selection, not turnover."""
    rng = random.Random(seed)

    sector_profile = {
        "Information Technology": (0.014, 0.055),
        "Financials": (0.008, 0.045),
        "Health Care": (0.009, 0.035),
        "Consumer Discretionary": (0.010, 0.050),
        "Communication Services": (0.009, 0.045),
        "Industrials": (0.008, 0.040),
        "Consumer Staples": (0.005, 0.025),
        "Energy": (0.007, 0.065),
        "Utilities": (0.004, 0.030),
        "Materials": (0.007, 0.045),
    }

    periods: list[Period] = []
    for month_index in range(n_months):
        bench_returns: dict[str, float] = {}
        port_returns: dict[str, float] = {}
        for sector in SECTORS:
            drift, vol = sector_profile[sector]
            r_bench = rng.gauss(drift, vol)
            alpha = SELECTION_ALPHA_BPS[sector]
            noise = rng.gauss(0.0, 0.004)
            bench_returns[sector] = r_bench
            port_returns[sector] = r_bench + alpha + noise
        periods.append(
            Period(
                label=f"2025-{month_index + 1:02d}",
                benchmark_returns=bench_returns,
                portfolio_returns=port_returns,
            )
        )
    return periods


def generate_sector_covariance(seed: int = 7) -> dict[str, dict[str, float]]:
    """A plausible sector-level covariance matrix built from a one-factor
    model: each sector loads on a shared market factor plus its own
    idiosyncratic variance. Guarantees a positive-semi-definite matrix by
    construction (Sigma = beta beta' * market_var + diag(idio_var)),
    the same trick a real factor-risk-model desk uses, just with one
    factor instead of many."""
    rng = random.Random(seed)
    market_var = 0.03**2

    betas = {
        "Information Technology": 1.35,
        "Financials": 1.10,
        "Health Care": 0.75,
        "Consumer Discretionary": 1.20,
        "Communication Services": 1.05,
        "Industrials": 1.00,
        "Consumer Staples": 0.55,
        "Energy": 0.90,
        "Utilities": 0.45,
        "Materials": 0.95,
    }
    idio_vol = {s: rng.uniform(0.02, 0.035) for s in SECTORS}

    cov: dict[str, dict[str, float]] = {i: {} for i in SECTORS}
    for i in SECTORS:
        for j in SECTORS:
            value = betas[i] * betas[j] * market_var
            if i == j:
                value += idio_vol[i] ** 2
            cov[i][j] = value
    return cov
