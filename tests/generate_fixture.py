"""
Deterministic test-fixture generator (no RNG, no network).

Run:  python tests/generate_fixture.py

Produces, under tests/fixtures/:
  - fixture_stock_data.csv   : a fixed, known 80-day Close-price series
  - expected_metrics.json    : golden risk-metric values + tolerances

The expected values are computed here by an INDEPENDENT reference
implementation (plain numpy, written from first principles) so that the
tests genuinely cross-check calculate_and_report.compute_risk_metrics
rather than re-using it (which would be a tautology).

Price-path design (so metrics are non-degenerate AND partly hand-checkable):
  - Segment A (days  0..24): rise 100 -> 150 with a small oscillation
  - Segment B (days 25..39): decline 150 -> 120  (the drawdown)
  - Segment C (days 40..79): recover 120 -> 140 with a small oscillation
  The global running peak is exactly 150.0 (day 24) and the lowest price
  after it is exactly 120.0 (day 39), so:
        Maximum Drawdown = (120 - 150) / 150 = -0.20  (exactly -20%)
  The oscillations give the log-return series real variance, so volatility,
  VaR and Sharpe are all non-degenerate.
"""
import os
import json
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
FIXTURE_DIR = os.path.join(HERE, "fixtures")
CSV_PATH = os.path.join(FIXTURE_DIR, "fixture_stock_data.csv")
JSON_PATH = os.path.join(FIXTURE_DIR, "expected_metrics.json")

N_DAYS = 80
PEAK_PRICE = 150.0   # exact global running max (day 24)
TROUGH_PRICE = 120.0  # exact min after the peak (day 39) -> MaxDD = -20%


def build_prices():
    prices = np.empty(N_DAYS)

    # Segment A: days 0..24, 100 -> 150 with +/-1% oscillation
    for i in range(0, 25):
        base = 100.0 + (PEAK_PRICE - 100.0) * (i / 24.0)
        prices[i] = base * (1.0 + 0.01 * np.sin(i * 0.9))
    prices[24] = PEAK_PRICE  # exact global peak

    # Segment B: days 25..39, 150 -> 120 with a tiny +/-0.5% oscillation
    for i in range(25, 40):
        frac = (i - 24) / (39 - 24)
        base = PEAK_PRICE + (TROUGH_PRICE - PEAK_PRICE) * frac
        prices[i] = base * (1.0 + 0.005 * np.sin(i * 1.1))
    prices[39] = TROUGH_PRICE  # exact trough after the peak

    # Segment C: days 40..79, 122 -> 140 with +/-1% oscillation.
    # Starts at 122 (not 120) so nothing dips below the day-39 trough,
    # keeping the -20% drawdown the unique global maximum drawdown.
    for i in range(40, N_DAYS):
        frac = (i - 39) / (N_DAYS - 1 - 39)
        base = 122.0 + (140.0 - 122.0) * frac
        prices[i] = base * (1.0 + 0.01 * np.sin(i * 0.7))

    return prices


def build_high_risk_prices():
    """
    Deterministic 80-day path with a GUARANTEED severe drawdown:
        peak 100.0 (day 19) -> trough 60.0 (day 39) == -40% (worse than -35%).
    Used to trigger the high-risk human-in-the-loop gate offline (no AAPL/yfinance).
    """
    n = 80
    prices = np.empty(n)
    peak, trough = 100.0, 60.0

    # Segment A: days 0..19 rise 80 -> 100
    for i in range(0, 20):
        base = 80.0 + (peak - 80.0) * (i / 19.0)
        prices[i] = base * (1.0 + 0.01 * np.sin(i * 0.9))
    prices[19] = peak  # exact global peak

    # Segment B: days 20..39 crash 100 -> 60 (the -40% drawdown)
    for i in range(20, 40):
        frac = (i - 19) / (39 - 19)
        base = peak + (trough - peak) * frac
        prices[i] = base * (1.0 + 0.005 * np.sin(i * 1.1))
    prices[39] = trough  # exact trough -> MaxDD = -40%

    # Segment C: days 40..79 partial recovery 62 -> 85 (stays above the trough)
    for i in range(40, n):
        frac = (i - 39) / (n - 1 - 39)
        base = 62.0 + (85.0 - 62.0) * frac
        prices[i] = base * (1.0 + 0.01 * np.sin(i * 0.7))

    return prices


def reference_metrics(close):
    """Independent first-principles reference (numpy, ddof=1 to match pandas.std)."""
    close = np.asarray(close, dtype=float)
    log_ret = np.diff(np.log(close))            # ln(P_t / P_{t-1})

    daily_std = log_ret.std(ddof=1)             # pandas Series.std() default = ddof=1
    ann_volatility = daily_std * np.sqrt(252)

    var_95 = -np.percentile(log_ret, 5)         # same convention as np.percentile in the app
    var_99 = -np.percentile(log_ret, 1)

    ann_return = log_ret.mean() * 252
    sharpe_ratio = ann_return / ann_volatility if ann_volatility != 0 else 0.0

    running_max = np.maximum.accumulate(close)
    drawdown = (close - running_max) / running_max
    max_drawdown = float(drawdown.min())

    return {
        "ann_volatility": float(ann_volatility),
        "var_95": float(var_95),
        "var_99": float(var_99),
        "sharpe_ratio": float(sharpe_ratio),
        "max_drawdown": max_drawdown,
    }


def main():
    os.makedirs(FIXTURE_DIR, exist_ok=True)

    prices = build_prices()
    dates = pd.bdate_range("2024-01-01", periods=N_DAYS)
    df = pd.DataFrame({"Close": np.round(prices, 6)}, index=dates)
    df.index.name = "Date"
    df.to_csv(CSV_PATH)

    # Compute golden values from the *written* CSV (round-trip safe).
    reloaded = pd.read_csv(CSV_PATH, parse_dates=["Date"], index_col="Date")
    metrics = reference_metrics(reloaded["Close"].values)

    payload = {
        "_description": "Golden risk metrics for fixture_stock_data.csv. "
                        "Computed by tests/generate_fixture.py (independent numpy reference).",
        "_provenance": {
            "n_days": N_DAYS,
            "designed_max_drawdown": -0.20,
            "peak_price": PEAK_PRICE,
            "trough_price": TROUGH_PRICE,
        },
        "tolerance_abs": 1e-6,
        **metrics,
    }
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    print(f"[OK] Wrote {CSV_PATH} ({N_DAYS} rows)")
    print(f"[OK] Wrote {JSON_PATH}")
    print("\nGolden metrics:")
    for k, v in metrics.items():
        print(f"  {k:<16}: {v:.10f}")
    # Sanity: the designed drawdown must be exactly -20%.
    assert abs(metrics["max_drawdown"] - (-0.20)) < 1e-9, metrics["max_drawdown"]
    print("\n[OK] Hand-checkable invariant verified: max_drawdown == -0.20")

    # --- High-risk fixture (for the human-in-the-loop gate tests) ---
    hr_prices = build_high_risk_prices()
    hr_dates = pd.bdate_range("2024-01-01", periods=N_DAYS)
    hr_df = pd.DataFrame({"Close": np.round(hr_prices, 6)}, index=hr_dates)
    hr_df.index.name = "Date"
    hr_csv = os.path.join(FIXTURE_DIR, "synthetic_high_risk_stock.csv")
    hr_df.to_csv(hr_csv)

    hr_reloaded = pd.read_csv(hr_csv, parse_dates=["Date"], index_col="Date")
    hr_metrics = reference_metrics(hr_reloaded["Close"].values)
    print(f"\n[OK] Wrote {hr_csv}")
    print(f"     synthetic high-risk max_drawdown = {hr_metrics['max_drawdown']:.4f}")
    # Sanity: must be guaranteed worse than -35% so it always trips the high-risk gate.
    assert hr_metrics["max_drawdown"] < -0.35, hr_metrics["max_drawdown"]
    print("[OK] High-risk invariant verified: max_drawdown < -0.35 (designed -0.40)")


if __name__ == "__main__":
    main()
