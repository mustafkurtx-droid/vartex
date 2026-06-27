# Vartex - Quick Start Guide

This guide shows you step-by-step how to run and verify the Vartex system via terminal.

---

## 1. Setup and Virtual Environment Activation

To make VarTex fully portable (e.g., when moving the project drive to another computer where the Python path or drive letter might change), we provide an automatic launcher script `run.bat` at the root of the project.

### Recommended (Portable / Auto-Heal):
Open your terminal in the project directory and run:
* **Using `run.bat`:**
  ```cmd
  run.bat [arguments]
  ```
  *This script will automatically detect your system Python, verify if the virtual environment is working, recreate it/reinstall dependencies if it is broken or was configured for another machine, and execute VarTex.*

### Manual Activation:
Alternatively, you can manually activate the virtual environment:
* **Windows PowerShell:**
  ```powershell
  .\venv\Scripts\Activate.ps1
  ```
* **Windows CMD:**
  ```cmd
  venv\Scripts\activate.bat
  ```

---

## 2. Single Stock Analysis Mode (Interactive)

To perform step-by-step interactive analysis for a single stock ticker:

```bash
python main.py THYAO.IS
```

### Prompt Flows (Human-in-the-Loop):
1. **Security & Data Fetching:** `requirements.txt` is audited and data is downloaded from Yahoo Finance.
2. **Approval Gate 1:** `[?] Stock data fetched successfully. Proceed to deterministic risk analysis? (y/n):`
   * Type `y` and press Enter to proceed.
3. **Approval Gate 2 (High Risk Check):** If the stock is flagged as high risk (e.g. Sharpe < 0, Volatility > 50%, Max DD < -30%; such as **AAPL**):
   * `Do you want to see the report? (y/n):`
   * Type `y` to view it, or `n` to abort without report generation.
4. **Approval Gate 3 (Monte Carlo):** `[?] Deterministic risk analysis report created. Proceed to Monte Carlo price simulation? (y/n):`
   * Type `y` to proceed.
5. **Approval Gate 4 (Comparison):** `[?] Monte Carlo price projection completed. Proceed to comparative VaR methodology analysis? (y/n):`
   * Type `y` to finalize the report.

---

## 3. Multi-Asset Portfolio Analysis Mode

To analyze any number of stocks and compare them against an equally-weighted portfolio with a specified investment amount ($):

```bash
python main.py --portfolio THYAO.IS AAPL GARAN.IS MSFT GOOGL --amount 10000
```

* The system sequentially prompts for verification on each stock ticker.
* Once all tickers are analyzed, it prompts for portfolio-level analysis:
  `[?] Selected stocks (THYAO.IS, AAPL, GARAN.IS, MSFT, GOOGL) analyzed successfully. Proceed to joint portfolio risk scenarios analysis? (y/n):`
* Type `y` and press Enter to generate `portfolio_report.md` and Monte Carlo portfolio charts.

---

## 4. Automatic (Non-Interactive) Mode

If you wish to skip all approval prompts and generate all reports automatically, append the `--no-interactive` flag:

* **Single Stock:**
  ```bash
  python main.py THYAO.IS --no-interactive
  ```
* **Portfolio Analysis:**
  ```bash
  python main.py --portfolio THYAO.IS AAPL GARAN.IS MSFT GOOGL --amount 10000 --no-interactive
  ```

---

## 5. Running Behavioral Integration Tests

To run the behavioral Gherkin scenario tests and update the test report table:

```bash
python run_tests.py
```

* This runs pytest integration tests in the background and updates `test_report.md` with the verified test states.
