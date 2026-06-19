import os
import sys
import shutil
import pytest
import subprocess

# Force tests to write outputs to test_outputs directory
os.environ["VARTEX_OUTPUT_DIR"] = "test_outputs"

WORKSPACE = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(WORKSPACE, "test_outputs")
REQUIREMENTS_PATH = os.path.join(WORKSPACE, "requirements.txt")

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
    # Scenario: High risk triggers human-in-the-loop approval mechanism (AAPL has DD > 30%)
    # In interactive mode, enters "n" when prompted to see report.
    cmd = [sys.executable, "main.py", "AAPL"]
    
    # We pass 'y' for the first prompt (deterministic risk analysis)
    # Then 'n' for the high risk report prompt
    env = os.environ.copy()
    env["FORCE_INTERACTIVE"] = "1"
    
    result = subprocess.run(
        cmd,
        input="y\nn\n",
        capture_output=True,
        text=True,
        env=env
    )
    
    # It should exit with 2 (or non-zero) and not generate report
    assert result.returncode == 2
    report_file = os.path.join(OUTPUT_DIR, "risk_report_AAPL.md")
    assert not os.path.exists(report_file)

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
