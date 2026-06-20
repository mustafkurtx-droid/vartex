import os
import sys
import json
import shutil
import pytest
import subprocess

import pandas as pd

# Force tests to write outputs to test_outputs directory
os.environ["VARTEX_OUTPUT_DIR"] = "test_outputs"

WORKSPACE = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(WORKSPACE, "test_outputs")
REQUIREMENTS_PATH = os.path.join(WORKSPACE, "requirements.txt")

# Offline fixtures (see tests/generate_fixture.py)
FIXTURE_DIR = os.path.join(WORKSPACE, "tests", "fixtures")
FIXTURE_CSV = os.path.join(FIXTURE_DIR, "fixture_stock_data.csv")            # normal, non-high-risk
EXPECTED_JSON = os.path.join(FIXTURE_DIR, "expected_metrics.json")
SYNTH_HIGH_RISK_CSV = os.path.join(FIXTURE_DIR, "synthetic_high_risk_stock.csv")  # -40% drawdown


def _seed_csv(ticker, src):
    """Place a fixture CSV where the sub-scripts expect it (so they skip yfinance)."""
    clean = ticker.replace(".", "_")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    dest = os.path.join(OUTPUT_DIR, f"{clean}_data.csv")
    shutil.copy2(src, dest)
    return dest


def _offline_main_env():
    """Env for orchestrator gate tests: interactive prompts, no PyPI security call."""
    env = os.environ.copy()
    env["FORCE_INTERACTIVE"] = "1"
    env["VARTEX_SKIP_SECURITY"] = "1"
    return env

def clean_outputs():
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

@pytest.fixture(autouse=True)
def setup_teardown():
    clean_outputs()
    yield
    # No need to clean after, so developers can inspect output

def test_normal_risk_analysis():
    # Scenario: Normal risk analysis with a valid ticker completes successfully
    cmd = [sys.executable, "main.py", "THYAO.IS", "--no-interactive"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    assert result.returncode == 0
    # Check that CSV is fetched and saved
    csv_file = os.path.join(OUTPUT_DIR, "THYAO_IS_data.csv")
    assert os.path.exists(csv_file)
    
    # Check report is generated
    report_file = os.path.join(OUTPUT_DIR, "risk_report_THYAO_IS.md")
    assert os.path.exists(report_file)
    
    with open(report_file, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Volatility, Sharpe, Max DD calculated
    assert "Volatility" in content or "volatility" in content or "Oynaklık" in content or "Volatility" in content
    assert "Sharpe" in content
    assert "Drawdown" in content or "drawdown" in content or "Maksimum" in content
    
    # Monte Carlo charts created
    chart_file = os.path.join(OUTPUT_DIR, "THYAO_IS_monte_carlo.png")
    assert os.path.exists(chart_file)
    
    # Comparative VaR steps completed (distribution chart and comparison table)
    hist_file = os.path.join(OUTPUT_DIR, "THYAO_IS_mc_returns_histogram.png")
    assert os.path.exists(hist_file)
    assert "Historical VaR vs. Monte Carlo VaR Comparison" in content

def test_invalid_ticker():
    # Scenario: Analysis fails and stops when an invalid or non-existent ticker is provided
    cmd = [sys.executable, "main.py", "XXXYZZ", "--no-interactive"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    # Return code of 1 should be returned
    assert result.returncode == 1
    # Check that error is in stdout/stderr and it stops immediately
    assert "Error" in result.stdout or "Error" in result.stderr or "failed" in result.stdout or "failed" in result.stderr
    # Verification that reports/charts are not created
    report_file = os.path.join(OUTPUT_DIR, "risk_report_XXXYZZ.md")
    assert not os.path.exists(report_file)

def test_risk_threshold_human_in_the_loop_cancel():
    # Scenario: High risk triggers human-in-the-loop approval; user answers "n".
    # OFFLINE: uses a synthetic -40% drawdown CSV instead of live AAPL/yfinance.
    # Exercises calculate_and_report.py directly (that is where the gate lives).
    ticker = "SYNTHRISK"
    _seed_csv(ticker, SYNTH_HIGH_RISK_CSV)
    report_file = os.path.join(OUTPUT_DIR, f"risk_report_{ticker}.md")

    env = os.environ.copy()
    env["FORCE_INTERACTIVE"] = "1"

    result = subprocess.run(
        [sys.executable, "calculate_and_report.py", ticker, "--report", report_file],
        input="n\n",
        capture_output=True,
        text=True,
        env=env,
    )

    # The high-risk condition must be detected, then the user's "n" stops it with exit 2.
    assert "HIGH RISK DETECTED" in result.stdout, result.stdout + result.stderr
    assert result.returncode == 2, result.stdout + result.stderr
    assert not os.path.exists(report_file)


def test_risk_threshold_human_in_the_loop_approve():
    # Scenario: High risk detected, but the user approves with "y" -> report IS generated.
    # OFFLINE: synthetic -40% drawdown CSV; calculate_and_report.py invoked directly.
    ticker = "SYNTHRISK"
    _seed_csv(ticker, SYNTH_HIGH_RISK_CSV)
    report_file = os.path.join(OUTPUT_DIR, f"risk_report_{ticker}.md")

    env = os.environ.copy()
    env["FORCE_INTERACTIVE"] = "1"

    result = subprocess.run(
        [sys.executable, "calculate_and_report.py", ticker, "--report", report_file],
        input="y\n",
        capture_output=True,
        text=True,
        env=env,
    )

    assert "HIGH RISK DETECTED" in result.stdout, result.stdout + result.stderr
    assert result.returncode == 0, result.stdout + result.stderr
    assert os.path.exists(report_file)
    with open(report_file, "r", encoding="utf-8") as f:
        content = f.read()
    assert "Sharpe" in content and "Drawdown" in content

def test_security_check_suspicious_package():
    # Scenario: Fake or hallucinated package detection halts orchestration
    # Backup requirements.txt
    backup_path = REQUIREMENTS_PATH + ".bak"
    shutil.copy2(REQUIREMENTS_PATH, backup_path)
    
    try:
        # Add fake package to requirements.txt
        with open(REQUIREMENTS_PATH, "a", encoding="utf-8") as f:
            f.write("\nthis-package-does-not-exist-on-pypi-12345==9.9.9\n")
            
        cmd = [sys.executable, "main.py", "THYAO.IS", "--no-interactive"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Abort process
        assert result.returncode == 1
        # English security report should be generated on disk
        sec_report = os.path.join(WORKSPACE, "security_report.md")
        assert os.path.exists(sec_report)
        
        with open(sec_report, "r", encoding="utf-8") as f:
            sec_content = f.read()
        assert "NOT FOUND" in sec_content or "Risk" in sec_content or "vulnerability" in sec_content.lower()
        
    finally:
        # Restore requirements.txt
        if os.path.exists(backup_path):
            shutil.copy2(backup_path, REQUIREMENTS_PATH)
            os.remove(backup_path)

def test_same_ticker_re_analysis_versioning():
    # Scenario: Re-analyzing same ticker preserves old report and creates versioned copy
    cmd = [sys.executable, "main.py", "THYAO.IS", "--no-interactive"]
    
    # Run first time
    res1 = subprocess.run(cmd, capture_output=True, text=True)
    assert res1.returncode == 0
    report_file = os.path.join(OUTPUT_DIR, "risk_report_THYAO_IS.md")
    assert os.path.exists(report_file)
    
    # Modify the first report slightly to check it's not overwritten
    with open(report_file, "a", encoding="utf-8") as f:
        f.write("\nUNIQUE_MARKER_FOR_TEST\n")
        
    # Run second time
    res2 = subprocess.run(cmd, capture_output=True, text=True)
    assert res2.returncode == 0
    
    # First report should still have marker
    with open(report_file, "r", encoding="utf-8") as f:
        content1 = f.read()
    assert "UNIQUE_MARKER_FOR_TEST" in content1
    
    # Second report should exist as version 1
    report_file_1 = os.path.join(OUTPUT_DIR, "risk_report_THYAO_IS_1.md")
    assert os.path.exists(report_file_1)


# ---------------------------------------------------------------------------
# Numeric-accuracy tests (offline, deterministic, no network / no yfinance).
#
# These verify the *values* produced by calculate_and_report.compute_risk_metrics()
# against golden numbers frozen in tests/fixtures/expected_metrics.json (computed
# by an independent reference in tests/generate_fixture.py). They read a fixed
# fixture CSV and call the pure helper directly, so they run in milliseconds.
# ---------------------------------------------------------------------------

from calculate_and_report import compute_risk_metrics


def _fixture_metrics():
    df = pd.read_csv(FIXTURE_CSV, parse_dates=["Date"], index_col="Date").dropna(subset=["Close"])
    return compute_risk_metrics(df)


def _expected():
    with open(EXPECTED_JSON, "r", encoding="utf-8") as f:
        return json.load(f)


def test_volatility_calculation_accuracy():
    # Annualized volatility = daily std(log returns) * sqrt(252)
    metrics = _fixture_metrics()
    exp = _expected()
    assert metrics["ann_volatility"] == pytest.approx(exp["ann_volatility"], abs=exp["tolerance_abs"])
    # Must be a real, non-degenerate volatility (guards against a zeroed/broken series).
    assert metrics["ann_volatility"] > 0.0


def test_var_95_calculation_accuracy():
    metrics = _fixture_metrics()
    exp = _expected()
    assert metrics["var_95"] == pytest.approx(exp["var_95"], abs=exp["tolerance_abs"])


def test_var_99_calculation_accuracy():
    metrics = _fixture_metrics()
    exp = _expected()
    assert metrics["var_99"] == pytest.approx(exp["var_99"], abs=exp["tolerance_abs"])
    # 99% VaR must be at least as severe as 95% VaR (catches a 95/99 mix-up).
    assert metrics["var_99"] >= metrics["var_95"]


def test_sharpe_ratio_calculation_accuracy():
    metrics = _fixture_metrics()
    exp = _expected()
    assert metrics["sharpe_ratio"] == pytest.approx(exp["sharpe_ratio"], abs=exp["tolerance_abs"])


def test_max_drawdown_calculation_accuracy():
    metrics = _fixture_metrics()
    exp = _expected()
    assert metrics["max_drawdown"] == pytest.approx(exp["max_drawdown"], abs=exp["tolerance_abs"])
    # Hand-checkable invariant: designed peak 150.0 -> trough 120.0 == exactly -20%.
    assert metrics["max_drawdown"] == pytest.approx(-0.20, abs=1e-9)


# ---------------------------------------------------------------------------
# Orchestrator approval-gate cancellation tests (offline via main.py --input-csv).
#
# These drive the real main.py orchestrator but feed it a fixed (normal, NON
# high-risk) fixture CSV and skip the PyPI security check, so no network is used.
# The normal fixture never trips the high-risk gate, keeping the stdin sequence
# clean (only main.py reads stdin; the sub-scripts do not prompt).
# ---------------------------------------------------------------------------

def test_approval_1_deterministic_cancel():
    # Onay 1 ("Proceed to deterministic risk analysis?") -> "n" -> exit 0, no report.
    ticker = "FIXNORM"
    report_file = os.path.join(OUTPUT_DIR, f"risk_report_{ticker}.md")
    result = subprocess.run(
        [sys.executable, "main.py", ticker, "--input-csv", FIXTURE_CSV],
        input="n\n",
        capture_output=True,
        text=True,
        env=_offline_main_env(),
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert not os.path.exists(report_file)


def test_approval_3_monte_carlo_cancel():
    # Onay 1 -> "y", Onay 3 ("Proceed to Monte Carlo?") -> "n".
    # Deterministic report exists, but no Monte Carlo chart is produced.
    ticker = "FIXNORM"
    report_file = os.path.join(OUTPUT_DIR, f"risk_report_{ticker}.md")
    mc_chart = os.path.join(OUTPUT_DIR, f"{ticker}_monte_carlo.png")
    result = subprocess.run(
        [sys.executable, "main.py", ticker, "--input-csv", FIXTURE_CSV],
        input="y\nn\n",
        capture_output=True,
        text=True,
        env=_offline_main_env(),
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert os.path.exists(report_file)          # Onay 1 passed -> report written
    assert not os.path.exists(mc_chart)         # Onay 3 cancelled -> no MC chart


def test_approval_4_comparison_cancel():
    # Onay 1 -> "y", Onay 3 -> "y", Onay 4 ("Proceed to comparative VaR?") -> "n".
    # Monte Carlo chart exists, but no comparison histogram / comparison section.
    ticker = "FIXNORM"
    report_file = os.path.join(OUTPUT_DIR, f"risk_report_{ticker}.md")
    mc_chart = os.path.join(OUTPUT_DIR, f"{ticker}_monte_carlo.png")
    hist_chart = os.path.join(OUTPUT_DIR, f"{ticker}_mc_returns_histogram.png")
    result = subprocess.run(
        [sys.executable, "main.py", ticker, "--input-csv", FIXTURE_CSV],
        input="y\ny\nn\n",
        capture_output=True,
        text=True,
        env=_offline_main_env(),
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert os.path.exists(mc_chart)             # Onay 3 passed -> MC chart exists
    assert not os.path.exists(hist_chart)       # Onay 4 cancelled -> no comparison histogram
    with open(report_file, "r", encoding="utf-8") as f:
        content = f.read()
    assert "Historical VaR vs. Monte Carlo VaR Comparison" not in content
