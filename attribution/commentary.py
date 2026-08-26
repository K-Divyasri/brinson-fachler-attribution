"""Plain-English summaries generated from the attribution numbers -- a
templated function reading real figures, not a call to a language model.
Same role as project 07's `commentary.py`: turn a table into two sentences
a portfolio manager would actually say out loud.
"""

from __future__ import annotations

from attribution.brinson_fachler import AttributionResult
from attribution.linking import LinkedAttributionResult
from attribution.risk import RiskAttributionResult


def _fmt_bps(x: float) -> str:
    return f"{x * 10_000:+.0f} bps"


def _fmt_pct(x: float) -> str:
    return f"{x * 100:+.2f}%"


def single_period_note(result: AttributionResult) -> str:
    lines = [
        f"Portfolio returned {_fmt_pct(result.portfolio_total_return)} vs. benchmark "
        f"{_fmt_pct(result.benchmark_total_return)}, active return {_fmt_pct(result.active_return)}.",
        f"Allocation contributed {_fmt_bps(result.total_allocation)}, selection "
        f"{_fmt_bps(result.total_selection)}, interaction {_fmt_bps(result.total_interaction)}.",
    ]

    best_alloc = max(result.sectors, key=lambda s: s.allocation)
    best_selection = max(result.sectors, key=lambda s: s.selection)
    worst_selection = min(result.sectors, key=lambda s: s.selection)

    lines.append(
        f"Biggest allocation win: {best_alloc.sector} ({_fmt_bps(best_alloc.allocation)}, "
        f"weighted {best_alloc.portfolio_weight * 100:.1f}% vs. benchmark {best_alloc.benchmark_weight * 100:.1f}%)."
    )
    if best_selection.selection > 0:
        lines.append(
            f"Best stock selection: {best_selection.sector} ({_fmt_bps(best_selection.selection)})."
        )
    if worst_selection.selection < 0:
        lines.append(
            f"Weakest stock selection: {worst_selection.sector} ({_fmt_bps(worst_selection.selection)})."
        )
    return " ".join(lines)


def linked_note(result: LinkedAttributionResult) -> str:
    n = len(result.period_labels)
    lines = [
        f"Over {n} periods ({result.period_labels[0]} to {result.period_labels[-1]}), the portfolio "
        f"compounded to {_fmt_pct(result.cumulative_portfolio_return)} vs. the benchmark's "
        f"{_fmt_pct(result.cumulative_benchmark_return)} -- {_fmt_pct(result.cumulative_active_return)} "
        f"cumulative active return, Carino-linked so it reconciles exactly.",
    ]
    total_allocation = sum(s.linked_allocation for s in result.sectors)
    total_selection = sum(s.linked_selection for s in result.sectors)
    lines.append(
        f"Linked allocation {_fmt_bps(total_allocation)}, linked selection {_fmt_bps(total_selection)}."
    )
    return " ".join(lines)


def risk_note(result: RiskAttributionResult) -> str:
    biggest = max(result.sectors, key=lambda s: s.component_contribution)
    smallest = min(result.sectors, key=lambda s: s.component_contribution)
    return (
        f"Portfolio monthly volatility: {result.portfolio_volatility * 100:.2f}%. "
        f"{biggest.sector} is the largest risk contributor ({biggest.pct_of_risk * 100:.1f}% of total "
        f"risk on a {biggest.weight * 100:.1f}% weight); {smallest.sector} contributes the least "
        f"({smallest.pct_of_risk * 100:.1f}%)."
    )
