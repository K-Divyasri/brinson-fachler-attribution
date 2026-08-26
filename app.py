"""Streamlit UI for the Brinson-Fachler Performance & Risk Attribution dashboard.

    streamlit run app.py

Pick a month (or the whole linked stretch), see where the portfolio's active
return actually came from - allocation, selection, or interaction - and then
flip to the risk tab to see where its volatility comes from instead.
"""

from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

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

st.set_page_config(page_title="Brinson-Fachler Attribution", page_icon=None, layout="wide")
st.title("Brinson-Fachler Performance & Risk Attribution")
st.caption(
    "Where did the active return come from - allocation, selection, or interaction? "
    "And where does the risk sit? Illustrative sector-level data, not live holdings. "
    "Educational, not investment advice."
)

with st.sidebar:
    st.header("Data")
    n_months = st.slider("Months of history", 3, 24, 12)
    seed = st.number_input("Random seed", 0, 9999, 7)
    st.caption(
        "Weights are fixed for the whole stretch (buy-and-hold). Portfolio overweights "
        "Tech and Energy, underweights Utilities and Staples; Energy and Financials "
        "carry a baked-in positive stock-selection edge, Materials a negative one."
    )

periods = generate_monthly_periods(n_months=n_months, seed=seed)

tab_single, tab_linked, tab_risk = st.tabs(
    ["Single period", "Linked (multi-period)", "Risk attribution"]
)

# --------------------------------------------------------------------------- #
# Single period
# --------------------------------------------------------------------------- #
with tab_single:
    labels = [p.label for p in periods]
    pick = st.selectbox("Month", labels, index=len(labels) - 1)
    period = next(p for p in periods if p.label == pick)

    result = brinson_fachler(
        PORTFOLIO_WEIGHTS, BENCHMARK_WEIGHTS, period.portfolio_returns, period.benchmark_returns
    )

    c1, c2, c3 = st.columns(3)
    c1.metric("Portfolio return", f"{result.portfolio_total_return * 100:.2f}%")
    c2.metric("Benchmark return", f"{result.benchmark_total_return * 100:.2f}%")
    c3.metric("Active return", f"{result.active_return * 100:+.2f}%")

    left, right = st.columns([1.2, 1])
    with left:
        rows = [
            {
                "Sector": s.sector,
                "Portfolio wt": f"{s.portfolio_weight * 100:.1f}%",
                "Benchmark wt": f"{s.benchmark_weight * 100:.1f}%",
                "Allocation (bps)": round(s.allocation * 10_000, 1),
                "Selection (bps)": round(s.selection * 10_000, 1),
                "Interaction (bps)": round(s.interaction * 10_000, 1),
                "Total (bps)": round(s.total * 10_000, 1),
            }
            for s in sorted(result.sectors, key=lambda s: -s.total)
        ]
        st.dataframe(rows, width="stretch", hide_index=True)
        st.caption(
            f"Reconciliation error: {result.reconciliation_error() * 10_000:.6f} bps "
            "(should be ~0 - every sector's total effect sums to the active return above)."
        )
    with right:
        sectors = [s.sector for s in result.sectors]
        fig = go.Figure()
        fig.add_trace(go.Bar(name="Allocation", x=sectors, y=[s.allocation * 10_000 for s in result.sectors]))
        fig.add_trace(go.Bar(name="Selection", x=sectors, y=[s.selection * 10_000 for s in result.sectors]))
        fig.add_trace(go.Bar(name="Interaction", x=sectors, y=[s.interaction * 10_000 for s in result.sectors]))
        fig.update_layout(
            barmode="relative", height=420, yaxis_title="effect (bps)", legend=dict(orientation="h")
        )
        st.plotly_chart(fig, width="stretch")

    st.markdown(single_period_note(result))

# --------------------------------------------------------------------------- #
# Linked multi-period
# --------------------------------------------------------------------------- #
with tab_linked:
    linked = link_periods(periods, PORTFOLIO_WEIGHTS, BENCHMARK_WEIGHTS)

    c1, c2, c3 = st.columns(3)
    c1.metric("Cumulative portfolio", f"{linked.cumulative_portfolio_return * 100:.2f}%")
    c2.metric("Cumulative benchmark", f"{linked.cumulative_benchmark_return * 100:.2f}%")
    c3.metric("Cumulative active", f"{linked.cumulative_active_return * 100:+.2f}%")

    left, right = st.columns([1.2, 1])
    with left:
        rows = [
            {
                "Sector": s.sector,
                "Linked allocation (bps)": round(s.linked_allocation * 10_000, 1),
                "Linked selection (bps)": round(s.linked_selection * 10_000, 1),
                "Linked interaction (bps)": round(s.linked_interaction * 10_000, 1),
                "Linked total (bps)": round(s.linked_total * 10_000, 1),
            }
            for s in sorted(linked.sectors, key=lambda s: -s.linked_total)
        ]
        st.dataframe(rows, width="stretch", hide_index=True)
        st.caption(
            f"Reconciliation error: {linked.reconciliation_error() * 10_000:.6f} bps over "
            f"{n_months} periods, Carino-linked (a naive unlinked sum would drift as the "
            "period count grows - try it in notebook 05)."
        )
    with right:
        cum_p, cum_b = 1.0, 1.0
        cum_portfolio, cum_benchmark = [], []
        for r in linked.period_results:
            cum_p *= 1 + r.portfolio_total_return
            cum_b *= 1 + r.benchmark_total_return
            cum_portfolio.append((cum_p - 1) * 100)
            cum_benchmark.append((cum_b - 1) * 100)
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=linked.period_labels, y=cum_portfolio, name="Portfolio (cumulative)"))
        fig.add_trace(go.Scatter(x=linked.period_labels, y=cum_benchmark, name="Benchmark (cumulative)"))
        fig.update_layout(height=420, yaxis_title="cumulative return (%)", legend=dict(orientation="h"))
        st.plotly_chart(fig, width="stretch")

    st.markdown(linked_note(linked))

# --------------------------------------------------------------------------- #
# Risk attribution
# --------------------------------------------------------------------------- #
with tab_risk:
    covariance = generate_sector_covariance(seed=seed)
    risk = component_risk_attribution(BENCHMARK_WEIGHTS, covariance)

    st.metric("Portfolio monthly volatility", f"{risk.portfolio_volatility * 100:.2f}%")

    left, right = st.columns([1.2, 1])
    with left:
        rows = [
            {
                "Sector": s.sector,
                "Weight": f"{s.weight * 100:.1f}%",
                "Marginal contribution": f"{s.marginal_contribution * 100:.2f}%",
                "Component contribution": f"{s.component_contribution * 100:.3f}%",
                "% of total risk": f"{s.pct_of_risk * 100:.1f}%",
            }
            for s in sorted(risk.sectors, key=lambda s: -s.component_contribution)
        ]
        st.dataframe(rows, width="stretch", hide_index=True)
        st.caption(f"Reconciliation error: {risk.reconciliation_error() * 100:.6f} pp of volatility.")
    with right:
        fig = go.Figure(
            go.Bar(
                x=[s.sector for s in risk.sectors],
                y=[s.pct_of_risk * 100 for s in risk.sectors],
            )
        )
        fig.update_layout(height=420, yaxis_title="% of total portfolio risk")
        st.plotly_chart(fig, width="stretch")

    st.markdown(risk_note(risk))
    st.caption(
        "Uses the benchmark's weights against a synthetic one-factor sector covariance "
        "matrix - swap in the portfolio's weights (or a real covariance estimate) to see "
        "the same decomposition for an actual book."
    )

st.divider()
st.caption(
    "Brinson-Fachler single-period decomposition, Carino (1999) multi-period linking, "
    "and Euler-theorem component risk attribution. All figures are computed from the "
    "synthetic data in attribution/data.py - see knowledge/ for the derivations."
)
