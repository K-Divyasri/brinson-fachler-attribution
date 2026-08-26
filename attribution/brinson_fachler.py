"""Single-period Brinson-Fachler performance attribution.

Decomposes active return (portfolio return minus benchmark return) into,
per sector:

    allocation_i  = (wp_i - wb_i) * (rb_i - Rb)
    selection_i   = wb_i * (rp_i - rb_i)
    interaction_i = (wp_i - wb_i) * (rp_i - rb_i)
    total_i       = allocation_i + selection_i + interaction_i

where Rb is the total benchmark return. Summing total_i across every
sector reproduces the portfolio's active return exactly -- that identity
is the thing every test in this module checks.

The `(rb_i - Rb)` term (subtracting the TOTAL benchmark return from each
sector's own return) is what makes this Brinson-FACHLER specifically,
distinct from the older Brinson-Hood-Beebower (1986) formula that uses
plain `rb_i`. The Fachler correction nets allocation to zero for a sector
that merely matches the market, which is the property real attribution
desks want.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SectorAttribution:
    sector: str
    portfolio_weight: float
    benchmark_weight: float
    portfolio_return: float
    benchmark_return: float
    allocation: float
    selection: float
    interaction: float

    @property
    def total(self) -> float:
        return self.allocation + self.selection + self.interaction


@dataclass
class AttributionResult:
    sectors: list[SectorAttribution]
    portfolio_total_return: float
    benchmark_total_return: float

    @property
    def active_return(self) -> float:
        return self.portfolio_total_return - self.benchmark_total_return

    @property
    def total_allocation(self) -> float:
        return sum(s.allocation for s in self.sectors)

    @property
    def total_selection(self) -> float:
        return sum(s.selection for s in self.sectors)

    @property
    def total_interaction(self) -> float:
        return sum(s.interaction for s in self.sectors)

    def reconciliation_error(self) -> float:
        """Should be ~0: sum of every sector's total effect must equal the
        active return. A nonzero value here means a bug, not a rounding
        quirk -- keep the tolerance tight in tests."""
        summed = sum(s.total for s in self.sectors)
        return summed - self.active_return


def _validate_weights(weights: dict[str, float], name: str) -> None:
    total = sum(weights.values())
    if abs(total - 1.0) > 1e-6:
        raise ValueError(f"{name} weights must sum to 1.0, got {total:.6f}")


def brinson_fachler(
    portfolio_weights: dict[str, float],
    benchmark_weights: dict[str, float],
    portfolio_returns: dict[str, float],
    benchmark_returns: dict[str, float],
) -> AttributionResult:
    """Compute single-period Brinson-Fachler attribution.

    All four dicts must share the exact same set of sector keys. Weights
    must each sum to 1.0 (a fully-invested long-only book on both sides --
    the classic textbook setup this formula assumes).
    """
    sectors = set(portfolio_weights)
    if sectors != set(benchmark_weights) or sectors != set(portfolio_returns) or sectors != set(benchmark_returns):
        raise ValueError("portfolio/benchmark weights and returns must share the same sector keys")

    _validate_weights(portfolio_weights, "portfolio")
    _validate_weights(benchmark_weights, "benchmark")

    benchmark_total_return = sum(benchmark_weights[s] * benchmark_returns[s] for s in sectors)
    portfolio_total_return = sum(portfolio_weights[s] * portfolio_returns[s] for s in sectors)

    rows: list[SectorAttribution] = []
    for sector in sorted(sectors):
        wp, wb = portfolio_weights[sector], benchmark_weights[sector]
        rp, rb = portfolio_returns[sector], benchmark_returns[sector]

        allocation = (wp - wb) * (rb - benchmark_total_return)
        selection = wb * (rp - rb)
        interaction = (wp - wb) * (rp - rb)

        rows.append(
            SectorAttribution(
                sector=sector,
                portfolio_weight=wp,
                benchmark_weight=wb,
                portfolio_return=rp,
                benchmark_return=rb,
                allocation=allocation,
                selection=selection,
                interaction=interaction,
            )
        )

    return AttributionResult(
        sectors=rows,
        portfolio_total_return=portfolio_total_return,
        benchmark_total_return=benchmark_total_return,
    )
