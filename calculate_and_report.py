import os
import sys
import numpy as np
import pandas as pd
from data_fetcher import fetch_stock_data


def compute_risk_metrics(df):
    """
    Pure, deterministic risk-metric computation. No I/O, no network, no prompts.

    Parameters
    ----------
    df : pandas.DataFrame
        Must contain a 'Close' column in chronological order.

    Returns
    -------
    dict with keys:
        ann_volatility, var_95, var_99, sharpe_ratio, max_drawdown,
        ann_return, daily_std

    Raises
    ------
    ValueError
        If a return series cannot be built (insufficient data).
    """
    df = df.copy()

    # Daily logarithmic return: ln(P_t / P_{t-1})
    df['Log_Return'] = np.log(df['Close'] / df['Close'].shift(1))
    log_returns = df['Log_Return'].dropna()

    if log_returns.empty:
        raise ValueError("Could not generate return series (insufficient data).")

    # Annualized volatility: daily standard deviation * sqrt(252)
    daily_std = log_returns.std()
    ann_volatility = daily_std * np.sqrt(252)

    # Historical VaR at 95% and 99% confidence levels
    var_95 = -np.percentile(log_returns, 5)
    var_99 = -np.percentile(log_returns, 1)

    # Sharpe Ratio (risk-free rate 0%)
    mean_daily_return = log_returns.mean()
    ann_return = mean_daily_return * 252
    sharpe_ratio = ann_return / ann_volatility if ann_volatility != 0 else 0.0

    # Maximum Drawdown
    prices = df['Close']
    roll_max = prices.cummax()
    drawdown = (prices - roll_max) / roll_max
    max_drawdown = drawdown.min()

    return {
        "ann_volatility": ann_volatility,
        "var_95": var_95,
        "var_99": var_99,
        "sharpe_ratio": sharpe_ratio,
        "max_drawdown": max_drawdown,
        "ann_return": ann_return,
        "daily_std": daily_std,
    }


def main():
    try:
        ticker = "THYAO.IS"
        report_path = None
        
        args = sys.argv[1:]
        
        # 1. Parse keyword arguments
        if "--ticker" in args:
            idx = args.index("--ticker")
            if idx + 1 < len(args):
                ticker = args[idx + 1]
        if "--report" in args:
            idx = args.index("--report")
            if idx + 1 < len(args):
                report_path = args[idx + 1]
                
        # 2. Extract positional arguments
        positionals = []
        i = 0
        while i < len(args):
            arg = args[i]
            if arg.startswith("-"):
                if arg in ("--ticker", "--report"):
                    i += 2
                else:
                    i += 1
            else:
                positionals.append(arg)
                i += 1
                
        # 3. Assign positional values if not already set by flags
        if "--ticker" not in args and len(positionals) > 0:
            ticker = positionals[0]
        if "--report" not in args and len(positionals) > 1:
            report_path = positionals[1]
            
        clean_ticker = ticker.replace(".", "_")
        output_dir = os.environ.get("VARTEX_OUTPUT_DIR", "outputs")
        csv_file = os.path.join(output_dir, "csv", f"{clean_ticker}_data.csv")
        
        if not report_path:
            report_path = os.path.join(output_dir, "md", f"risk_report_{clean_ticker}.md")
        
        # 1. Load data and clean NaNs
        try:
            if os.path.exists(csv_file):
                print(f"Loading existing data file '{csv_file}'...")
                df = pd.read_csv(csv_file, parse_dates=['Date'], index_col='Date').dropna(subset=['Close'])
            else:
                print(f"'{csv_file}' not found, downloading fresh data...")
                df = fetch_stock_data(ticker, period="2y", save_csv=True)
        except Exception as e:
            print(f"Error: An unexpected issue occurred while loading or fetching the data file: {str(e)}")
            sys.exit(1)
            
        if df.empty:
            print(f"Error: No data available to analyze for {ticker}.")
            sys.exit(1)

        # 2. Risk calculations (delegated to the pure, testable helper)
        try:
            metrics = compute_risk_metrics(df)
            ann_volatility = metrics["ann_volatility"]
            var_95 = metrics["var_95"]
            var_99 = metrics["var_99"]
            sharpe_ratio = metrics["sharpe_ratio"]
            max_drawdown = metrics["max_drawdown"]
        except ValueError as e:
            # Insufficient data to build a return series.
            print(f"Error: {str(e)} ({ticker})")
            sys.exit(1)
        except Exception as e:
            print(f"Error: An error occurred while calculating mathematical risk metrics: {str(e)}")
            sys.exit(1)
            
        # 3. High Risk and Threshold Checks
        # Thresholds: Max DD < -30% OR Sharpe < 0 OR Volatility > 50%
        is_high_risk = (max_drawdown < -0.30) or (sharpe_ratio < 0.0) or (ann_volatility > 0.50)
        no_interactive = "--no-interactive" in sys.argv
        
        if is_high_risk:
            print("\n" + "!"*60)
            print("  HIGH RISK DETECTED")
            print("  Risk metrics for this stock are at critical levels.")
            print("!"*60)
            print(f"  - Annual Volatility  : {ann_volatility*100:.2f}% (Threshold: >50.00%)")
            print(f"  - Sharpe Ratio       : {sharpe_ratio:.4f} (Threshold: <0.00)")
            print(f"  - Maximum Loss (DD)  : {max_drawdown*100:.2f}% (Threshold: <-30.00%)")
            print("!"*60)
            
            # Ask for user approval if interactive mode is enabled
            is_interactive = sys.stdin.isatty() or os.environ.get("FORCE_INTERACTIVE") == "1"
            if not no_interactive and is_interactive:
                while True:
                    try:
                        choice = input("\nDo you want to see the report? (y/n): ").strip().lower()
                        if choice == 'y':
                            print("Approved. Generating report...")
                            break
                        elif choice == 'n':
                            print("\nProcess stopped by user request. Report not generated.")
                            sys.exit(2) # Special exit code 2: User chose not to generate the report
                        else:
                            print("Invalid input. Please type 'y' or 'n'.")
                    except (EOFError, KeyboardInterrupt):
                        print("\nProcess cancelled.")
                        sys.exit(2)
            else:
                print("\nNon-interactive mode: High risk detection approved, generating report automatically...")
                
        # Console output (Deterministic Results)
        print("\n" + "="*60)
        print(f"  {ticker} DETERMINISTIC RISK METRICS (Last 2 Years)")
        print("="*60)
        print(f"1. Annual Volatility (Log Returns): {ann_volatility*100:.2f}%")
        print(f"2. Historical VaR 95%               : {var_95*100:.2f}%")
        print(f"3. Historical VaR 99%               : {var_99*100:.2f}%")
        print(f"4. Sharpe Ratio (Rf = 0%)           : {sharpe_ratio:.4f}")
        print(f"5. Maximum Drawdown (Max DD)        : {max_drawdown*100:.2f}%")
        print("="*60)
        
        # 4. Report Writing Phase
        try:
            # report_path is already resolved at the start of main
            
            report_content = f"""# {ticker} Stock Risk Report

This report includes the risk metrics calculated using purely deterministic Python code, based on the last 2 years of daily closing prices for **{ticker}** fetched via yfinance.

## Calculated Risk Metrics

| Risk Metric | Calculated Value | Description |
| :--- | :--- | :--- |
| **Annualized Volatility** | {ann_volatility*100:.2f}% | Annualized daily standard deviation of log returns (based on 252 trading days). Represents price variance. |
| **Historical VaR (95% Confidence)** | {var_95*100:.2f}% | Indicates that daily loss will not exceed this rate with 95% probability based on historical data. |
| **Historical VaR (99% Confidence)** | {var_99*100:.2f}% | Indicates that daily loss will not exceed this rate with 99% probability based on historical data (extreme risk). |
| **Sharpe Ratio (Rf = 0%)** | {sharpe_ratio:.4f} | Annualized log returns divided by annualized volatility. Performance per unit of risk. |
| **Maximum Drawdown (Max DD)** | {max_drawdown*100:.2f}% | The largest percentage loss recorded from peak to trough over the last 2 years. |

## Methodology and Explanations

1. **Log Returns:** Logarithmic returns ($R_t = \\ln(P_t / P_{{t-1}})$) are used instead of simple returns due to statistical properties (symmetry, closer to normality) and additive properties over time.
2. **Historical VaR (Value at Risk):** Historical log returns are sorted from worst to best, and thresholds for the worst 5% (95% confidence) and worst 1% (99% confidence) are determined.
3. **Maximum Drawdown (Maximum Drawdown):** Measures the worst-case scenario loss if an investor buys at the peak and sells at the trough.

*Note: This report is calculated entirely using deterministic Python code. It does not contain AI predictions or probabilistic inferences.*
"""

            os.makedirs(os.path.dirname(report_path), exist_ok=True)
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(report_content)
            print(f"\nEnglish risk report successfully saved to '{report_path}'.")
        except Exception as e:
            print(f"Error: An error occurred while writing the report file to disk: {str(e)}")
            sys.exit(1)
            
    except Exception as e:
        print(f"System Error (calculate_and_report): {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
