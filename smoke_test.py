"""Offline end-to-end sanity check, no Streamlit involved.

    python smoke_test.py

Runs single-period attribution, multi-period linking, and risk attribution
on the synthetic demo data and checks every reconciliation identity holds.
Exits non-zero if anything is off.
"""

from __future__ import annotations

import sys

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

TOLERANCE = 1e-8


def main() -> int:
    periods = generate_monthly_periods(n_months=12, seed=7)

    single = brinson_fachler(
        PORTFOLIO_WEIGHTS, BENCHMARK_WEIGHTS, periods[-1].portfolio_returns, periods[-1].benchmark_returns
    )
    print(f"[single period, {periods[-1].label}]")
    print(single_period_note(single))
    err = abs(single.reconciliation_error())
    print(f"reconciliation error: {err:.2e}")
    if err > TOLERANCE:
        print("FAIL: single-period reconciliation error too large")
        return 1

    linked = link_periods(periods, PORTFOLIO_WEIGHTS, BENCHMARK_WEIGHTS)
    print(f"\n[linked, {len(periods)} periods]")
    print(linked_note(linked))
    err = abs(linked.reconciliation_error())
    print(f"reconciliation error: {err:.2e}")
    if err > TOLERANCE:
        print("FAIL: linked reconciliation error too large")
        return 1

    covariance = generate_sector_covariance()
    risk = component_risk_attribution(BENCHMARK_WEIGHTS, covariance)
    print("\n[risk attribution]")
    print(risk_note(risk))
    err = abs(risk.reconciliation_error())
    print(f"reconciliation error: {err:.2e}")
    if err > TOLERANCE:
        print("FAIL: risk reconciliation error too large")
        return 1

    print("\nOK: all reconciliation identities hold.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
