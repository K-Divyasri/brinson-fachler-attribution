"""Multi-period linking of Brinson-Fachler attribution (Carino, 1999).

A single-period attribution reconciles perfectly: allocation + selection +
interaction = active return, for that one period. But you can't just SUM
each sector's effect across many periods and expect the total to equal
the *cumulative geometric* active return -- returns compound, attribution
effects don't, and naive summation is off by a growing amount as the
number of periods increases.

Carino's fix: convert each period's active return into "log space" via a
period-specific scaling factor `k_t`, sum in log space (where compounding
IS additive), then convert back. The scaling factor is:

    k_t = (ln(1 + Rp_t) - ln(1 + Rb_t)) / (Rp_t - Rb_t)

with the limit `k_t = 1 / (1 + Rb_t)` when `Rp_t == Rb_t` (both branches of
that quotient go to zero, so L'Hopital's rule gives the derivative
instead). A single scaling factor `K` plays the same role for the whole
multi-period stretch, using cumulative geometric returns instead of a
single period's. Each period's per-sector effect gets multiplied by
`k_t / K` before summing across periods -- that ratio is what makes the
whole thing reconcile.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from attribution.brinson_fachler import AttributionResult, brinson_fachler
from attribution.data import Period


def _carino_factor(r_portfolio: float, r_benchmark: float) -> float:
    if abs(r_portfolio - r_benchmark) < 1e-12:
        return 1.0 / (1.0 + r_benchmark)
    return (math.log1p(r_portfolio) - math.log1p(r_benchmark)) / (r_portfolio - r_benchmark)


def _geometric_cumulative(returns: list[float]) -> float:
    product = 1.0
    for r in returns:
        product *= 1.0 + r
    return product - 1.0


@dataclass
class LinkedSectorAttribution:
    sector: str
    linked_allocation: float
    linked_selection: float
    linked_interaction: float

    @property
    def linked_total(self) -> float:
        return self.linked_allocation + self.linked_selection + self.linked_interaction


@dataclass
class LinkedAttributionResult:
    period_labels: list[str]
    period_results: list[AttributionResult]
    sectors: list[LinkedSectorAttribution]
    cumulative_portfolio_return: float
    cumulative_benchmark_return: float

    @property
    def cumulative_active_return(self) -> float:
        return self.cumulative_portfolio_return - self.cumulative_benchmark_return

    def reconciliation_error(self) -> float:
        """Should be ~0: every sector's linked total, summed, must equal
        the cumulative geometric active return over the whole stretch."""
        summed = sum(s.linked_total for s in self.sectors)
        return summed - self.cumulative_active_return


def link_periods(
    periods: list[Period],
    portfolio_weights: dict[str, float],
    benchmark_weights: dict[str, float],
) -> LinkedAttributionResult:
    """Run single-period Brinson-Fachler on every period, then link the
    results together with Carino smoothing so they reconcile to the
    cumulative (compounded) active return instead of a naive sum.

    Weights are held static across the whole stretch (a buy-and-hold
    allocation, matching how `data.generate_monthly_periods` builds its
    demo periods) -- pass the same two weight dicts you'd pass to a single
    call to `brinson_fachler`.
    """
    if not periods:
        raise ValueError("need at least one period to link")

    period_results: list[AttributionResult] = []
    period_factors: list[float] = []
    for period in periods:
        result = brinson_fachler(
            portfolio_weights, benchmark_weights, period.portfolio_returns, period.benchmark_returns
        )
        period_results.append(result)
        period_factors.append(_carino_factor(result.portfolio_total_return, result.benchmark_total_return))

    portfolio_returns = [r.portfolio_total_return for r in period_results]
    benchmark_returns = [r.benchmark_total_return for r in period_results]
    cum_portfolio = _geometric_cumulative(portfolio_returns)
    cum_benchmark = _geometric_cumulative(benchmark_returns)
    total_factor = _carino_factor(cum_portfolio, cum_benchmark)

    sector_names = sorted({s.sector for r in period_results for s in r.sectors})
    linked_allocation = dict.fromkeys(sector_names, 0.0)
    linked_selection = dict.fromkeys(sector_names, 0.0)
    linked_interaction = dict.fromkeys(sector_names, 0.0)

    for result, k_t in zip(period_results, period_factors):
        scale = k_t / total_factor
        for sector_row in result.sectors:
            linked_allocation[sector_row.sector] += sector_row.allocation * scale
            linked_selection[sector_row.sector] += sector_row.selection * scale
            linked_interaction[sector_row.sector] += sector_row.interaction * scale

    linked_sectors = [
        LinkedSectorAttribution(
            sector=sector,
            linked_allocation=linked_allocation[sector],
            linked_selection=linked_selection[sector],
            linked_interaction=linked_interaction[sector],
        )
        for sector in sector_names
    ]

    return LinkedAttributionResult(
        period_labels=[p.label for p in periods],
        period_results=period_results,
        sectors=linked_sectors,
        cumulative_portfolio_return=cum_portfolio,
        cumulative_benchmark_return=cum_benchmark,
    )
