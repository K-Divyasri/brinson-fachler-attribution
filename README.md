# Brinson-Fachler Performance & Risk Attribution

Most "attribution dashboards" show a bar chart with no formula behind it. This one
implements the actual Brinson-Fachler decomposition by hand - allocation, selection,
interaction - proves it reconciles to the active return exactly, links it across
periods the way a real performance team does (Carino, 1999), and adds the risk side
too: an Euler-theorem component-risk breakdown that answers "where does the
volatility come from," not just "where did the return come from."

> **Educational project, not financial advice.**

---

## Why this is the differentiator

A Brinson chart with no reconciliation check is decoration - there's no way to tell
if the formula was implemented correctly, or with a sign flipped, or with the wrong
benchmark term (Brinson-Hood-Beebower's plain `rb_i` instead of Fachler's
`(rb_i - Rb)`). Every result in this project asserts its own reconciliation
identity:

- **Single period**: `allocation + selection + interaction == active return`,
  sector by sector, to within floating-point noise.
- **Multi-period (linked)**: the Carino-linked sum of every period's effects equals
  the *cumulative geometric* active return - not the naive sum, which drifts once
  compounding matters (there's a test proving the naive sum is wrong).
- **Risk attribution**: every sector's component contribution to risk sums to
  total portfolio volatility exactly (Euler's theorem for homogeneous functions).

Showing the reconciliation, not just the chart, is the skill that matters in
practice: "performance attribution, factor-based and Brinson approaches."

---

## What it computes

**Performance attribution (`attribution/brinson_fachler.py`)**
- Per-sector allocation, selection, and interaction effects
- Brinson-**Fachler** specifically: allocation uses `(rb_i - Rb)`, the correction
  that zeroes out allocation for a sector that just matches the market

**Multi-period linking (`attribution/linking.py`)**
- Carino (1999) log-linking so per-period effects compound correctly across any
  number of periods

**Risk attribution (`attribution/risk.py`)**
- Marginal and component contribution to risk by sector, from a covariance matrix,
  via Euler's theorem - no approximation, no residual

**Plain-English commentary (`attribution/commentary.py`)**
- Templated sentences reading the real numbers, not a language-model call

---

## Project structure

```
brinson-fachler-attribution/
├── app.py                  # Streamlit dashboard: single-period, linked, and risk tabs
├── requirements.txt
├── smoke_test.py            # offline end-to-end check + reconciliation asserts
└── attribution/
    ├── data.py               # synthetic sector weights/returns/covariance (illustrative)
    ├── brinson_fachler.py    # single-period allocation/selection/interaction
    ├── linking.py            # Carino multi-period linking
    ├── risk.py               # component/marginal risk contribution
    └── commentary.py         # plain-English summaries from the real figures
```

---

## Run it locally

```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # macOS/Linux

pip install -r requirements.txt

python smoke_test.py     # offline sanity check + reconciliation
pytest -q                # 20 tests, incl. a hand-computed 2-sector golden example
streamlit run app.py     # UI at http://localhost:8501
```

---

## Use it from code

```python
from attribution.brinson_fachler import brinson_fachler
from attribution.data import BENCHMARK_WEIGHTS, PORTFOLIO_WEIGHTS, generate_monthly_periods
from attribution.linking import link_periods

periods = generate_monthly_periods(n_months=12, seed=7)
single = brinson_fachler(
    PORTFOLIO_WEIGHTS, BENCHMARK_WEIGHTS,
    periods[-1].portfolio_returns, periods[-1].benchmark_returns,
)
single.active_return, single.reconciliation_error()

linked = link_periods(periods, PORTFOLIO_WEIGHTS, BENCHMARK_WEIGHTS)
linked.cumulative_active_return, linked.reconciliation_error()
```

---

## Deploy free

- **Streamlit Community Cloud** (free, no card) - point it at `app.py`.
- **Hugging Face Spaces** (Streamlit SDK, free).
- **Docker** (`Dockerfile` included, verified: builds, runs, `/_stcore/health` returns
  200) on Render/Railway/Fly - reads `$PORT`.

No API keys, no paid services - synthetic sector data only.

---

## Extending it (v2 ideas)

- Swap the synthetic sector data for real 13F/holdings-based weights and real
  factor-model covariance (Barra/Axioma-style) - the attribution and risk math
  don't change, only `data.py` does.
- Add a second attribution level (sector -> individual security) for full
  top-down/bottom-up drill-through.
- Compare Brinson-Fachler against Brinson-Hood-Beebower side by side to show why
  the Fachler correction matters on a sector that merely tracks the benchmark.

## Honest limitations

- Single-currency, single-asset-class attribution; no currency/hedging effect
  (a real global-equity attribution needs a fourth term for that).
- Weights are static across the whole linked stretch (no intra-period trading) -
  a real desk would need daily or at-least-monthly weight snapshots.
- The covariance matrix is a synthetic one-factor construction, not an estimated
  factor-model covariance from real returns.

## License
MIT - do whatever you like, no warranty.
