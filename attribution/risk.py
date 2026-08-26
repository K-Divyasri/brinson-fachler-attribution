"""Component and marginal contribution to risk, by sector.

Performance attribution answers "where did the *return* come from."
This answers the other half of the roadmap's "Performance & Risk
Attribution" title: "where does the portfolio's *volatility* come from."

Portfolio variance is a homogeneous degree-1 function of the weight
vector, so Euler's theorem gives an exact decomposition with no
approximation and no residual:

    portfolio_variance = w' Sigma w
    marginal_contribution_i  = (Sigma w)_i / portfolio_vol
    component_contribution_i = w_i * marginal_contribution_i

and by construction `sum_i component_contribution_i == portfolio_vol`
exactly -- every dollar (or percentage point) of volatility is assigned
to some sector, nothing left over.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SectorRiskContribution:
    sector: str
    weight: float
    marginal_contribution: float
    component_contribution: float
    pct_of_risk: float


@dataclass
class RiskAttributionResult:
    sectors: list[SectorRiskContribution]
    portfolio_volatility: float

    def reconciliation_error(self) -> float:
        """Should be ~0: every sector's component contribution, summed,
        must equal total portfolio volatility (Euler's theorem)."""
        return sum(s.component_contribution for s in self.sectors) - self.portfolio_volatility


def _weights_to_vector(weights: dict[str, float], sectors: list[str]) -> list[float]:
    return [weights[s] for s in sectors]


def _matvec(matrix: dict[str, dict[str, float]], sectors: list[str], vector: list[float]) -> list[float]:
    return [sum(matrix[row][col] * vector[j] for j, col in enumerate(sectors)) for row in sectors]


def component_risk_attribution(
    weights: dict[str, float],
    covariance: dict[str, dict[str, float]],
) -> RiskAttributionResult:
    """Decompose portfolio volatility into a per-sector contribution.

    `covariance` is a sector x sector dict of dicts (as produced by
    `data.generate_sector_covariance`), in the same return units as
    `weights` (e.g. monthly fractional variance/covariance).
    """
    sectors = sorted(weights)
    if set(covariance) != set(sectors) or any(set(covariance[s]) != set(sectors) for s in sectors):
        raise ValueError("covariance matrix must be square over exactly the weighted sectors")

    w = _weights_to_vector(weights, sectors)
    sigma_w = _matvec(covariance, sectors, w)
    portfolio_variance = sum(wi * swi for wi, swi in zip(w, sigma_w))
    if portfolio_variance < 0:
        raise ValueError("covariance matrix produced a negative portfolio variance -- not positive semi-definite")
    portfolio_vol = portfolio_variance**0.5

    rows: list[SectorRiskContribution] = []
    for sector, wi, swi in zip(sectors, w, sigma_w):
        marginal = swi / portfolio_vol if portfolio_vol > 0 else 0.0
        component = wi * marginal
        pct = component / portfolio_vol if portfolio_vol > 0 else 0.0
        rows.append(
            SectorRiskContribution(
                sector=sector,
                weight=wi,
                marginal_contribution=marginal,
                component_contribution=component,
                pct_of_risk=pct,
            )
        )

    return RiskAttributionResult(sectors=rows, portfolio_volatility=portfolio_vol)
