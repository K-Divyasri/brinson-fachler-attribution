import pytest

from attribution.brinson_fachler import brinson_fachler


def test_hand_computed_two_sector_example():
    """Hand-derived golden numbers (see knowledge/ for the worked-by-hand
    derivation): a 2-sector book where allocation, selection, and
    interaction all come out to clean numbers -- a real bug (e.g. a sign
    flip, or using Brinson-Hood-Beebower's rb_i instead of Fachler's
    (rb_i - Rb)) would move these off their exact values, not just add
    noise."""
    wp = {"A": 0.6, "B": 0.4}
    wb = {"A": 0.5, "B": 0.5}
    rp = {"A": 0.10, "B": 0.02}
    rb = {"A": 0.08, "B": 0.04}

    result = brinson_fachler(wp, wb, rp, rb)

    assert result.benchmark_total_return == pytest.approx(0.06)
    assert result.portfolio_total_return == pytest.approx(0.068)
    assert result.active_return == pytest.approx(0.008)

    assert result.total_allocation == pytest.approx(0.004)
    assert result.total_selection == pytest.approx(0.0)
    assert result.total_interaction == pytest.approx(0.004)
    assert result.reconciliation_error() == pytest.approx(0.0, abs=1e-12)

    sector_a = next(s for s in result.sectors if s.sector == "A")
    sector_b = next(s for s in result.sectors if s.sector == "B")
    assert sector_a.allocation == pytest.approx(0.002)
    assert sector_b.allocation == pytest.approx(0.002)
    assert sector_a.selection == pytest.approx(0.01)
    assert sector_b.selection == pytest.approx(-0.01)
    assert sector_a.interaction == pytest.approx(0.002)
    assert sector_b.interaction == pytest.approx(0.002)


def test_matching_weights_zero_allocation():
    """If the portfolio holds the benchmark's exact weights, allocation
    must be zero for every sector -- there's no over/underweight bet to
    score."""
    wp = wb = {"A": 0.5, "B": 0.5}
    rp = {"A": 0.03, "B": -0.01}
    rb = {"A": 0.02, "B": 0.00}
    result = brinson_fachler(wp, wb, rp, rb)
    assert result.total_allocation == pytest.approx(0.0)
    assert result.total_interaction == pytest.approx(0.0)
    # with no weight bets, active return is pure stock selection
    assert result.total_selection == pytest.approx(result.active_return)


def test_matching_returns_zero_selection_and_interaction():
    """If every sector's portfolio return equals its benchmark return,
    active return must be pure allocation."""
    wp = {"A": 0.7, "B": 0.3}
    wb = {"A": 0.4, "B": 0.6}
    rp = rb = {"A": 0.05, "B": 0.01}
    result = brinson_fachler(wp, wb, rp, rb)
    assert result.total_selection == pytest.approx(0.0)
    assert result.total_interaction == pytest.approx(0.0)
    assert result.total_allocation == pytest.approx(result.active_return)


def test_reconciliation_holds_on_larger_random_book():
    import random

    rng = random.Random(42)
    sectors = [f"S{i}" for i in range(8)]
    raw_wp = [rng.uniform(1, 10) for _ in sectors]
    raw_wb = [rng.uniform(1, 10) for _ in sectors]
    wp = {s: w / sum(raw_wp) for s, w in zip(sectors, raw_wp)}
    wb = {s: w / sum(raw_wb) for s, w in zip(sectors, raw_wb)}
    rp = {s: rng.gauss(0.01, 0.05) for s in sectors}
    rb = {s: rng.gauss(0.008, 0.04) for s in sectors}

    result = brinson_fachler(wp, wb, rp, rb)
    assert result.reconciliation_error() == pytest.approx(0.0, abs=1e-12)


def test_mismatched_sectors_raise():
    wp = {"A": 1.0}
    wb = {"B": 1.0}
    with pytest.raises(ValueError, match="sector keys"):
        brinson_fachler(wp, wb, {"A": 0.1}, {"B": 0.1})


def test_weights_must_sum_to_one():
    wp = {"A": 0.4, "B": 0.4}  # sums to 0.8, not 1.0
    wb = {"A": 0.5, "B": 0.5}
    with pytest.raises(ValueError, match="sum to 1.0"):
        brinson_fachler(wp, wb, {"A": 0.1, "B": 0.1}, {"A": 0.1, "B": 0.1})
