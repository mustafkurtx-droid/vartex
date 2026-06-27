import os
import sys
import argparse
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def main():
    parser = argparse.ArgumentParser(description="N-Asset Portfolio Risk Analysis Module")
    parser.add_argument("--tickers", type=str, nargs="+", required=True)
    parser.add_argument("--amount", type=float, required=True)
    parser.add_argument("--report", type=str, required=False, default=None)
    
    args = parser.parse_args()
    tickers = args.tickers
    amount = args.amount
    report_file = args.report
    
    output_dir = os.environ.get("VARTEX_OUTPUT_DIR", "outputs")
    N = len(tickers)
    clean_tickers = [t.replace(".", "_") for t in tickers]
    if not report_file:
        ticker_comb = "_".join(clean_tickers[:3])
        report_file = os.path.join(output_dir, "md", f"portfolio_report_{ticker_comb}.md")
    
    # 1. Load and merge data
    dfs = []
    for t in tickers:
        clean_t = t.replace(".", "_")
        csv_file = os.path.join(output_dir, "csv", f"{clean_t}_data.csv")
        if not os.path.exists(csv_file):
            print(f"Error: {csv_file} not found.")
            sys.exit(1)
        df_t = pd.read_csv(csv_file, parse_dates=['Date'], index_col='Date').dropna(subset=['Close'])
        df_t = df_t[['Close']].rename(columns={'Close': f'Close_{clean_t}'})
        dfs.append(df_t)
        
    df = dfs[0]
    for next_df in dfs[1:]:
        df = pd.merge(df, next_df, left_index=True, right_index=True)
        
    if df.empty:
        print("Error: No overlapping historical data found for the selected stock tickers.")
        sys.exit(1)
        
    # 2. Calculate log returns
    returns_df = pd.DataFrame(index=df.index)
    for t in tickers:
        clean_t = t.replace(".", "_")
        returns_df[f'Return_{clean_t}'] = np.log(df[f'Close_{clean_t}'] / df[f'Close_{clean_t}'].shift(1))
    returns_df = returns_df.dropna()
    
    # Correlation Matrix
    corr_matrix = returns_df.corr()
    
    # Portfolio return (Equally Weighted: 1 / N)
    weights = np.ones(N) / N
    return_cols = [f'Return_{ct}' for ct in clean_tickers]
    returns_df['Port_Return'] = returns_df[return_cols].dot(weights)
    
    # 3. Calculate Risk Metrics
    # Volatilities
    vols = {}
    vols_dolar = {}
    for t, ct in zip(tickers, clean_tickers):
        v = returns_df[f'Return_{ct}'].std() * np.sqrt(252)
        vols[t] = v
        vols_dolar[t] = amount * v
        
    port_vol = returns_df['Port_Return'].std() * np.sqrt(252)
    port_vol_dolar = amount * port_vol
    
    # Daily Historical VaR
    var_95_dolar_single = {}
    var_99_dolar_single = {}
    for t, ct in zip(tickers, clean_tickers):
        var_95_dolar_single[t] = amount * (-np.percentile(returns_df[f'Return_{ct}'], 5))
        var_99_dolar_single[t] = amount * (-np.percentile(returns_df[f'Return_{ct}'], 1))
        
    var_95_dolar_port = amount * (-np.percentile(returns_df['Port_Return'], 5))
    var_99_dolar_port = amount * (-np.percentile(returns_df['Port_Return'], 1))
    
    # 4. Monte Carlo Simulation (21 Days, 10,000 trials)
    def run_mc_simulation(mu, sigma, s0):
        np.random.seed(42)
        N_days = 21
        M_paths = 10000
        dt = 1
        sim_paths = np.zeros((N_days + 1, M_paths))
        sim_paths[0] = s0
        for t in range(1, N_days + 1):
            sim_paths[t] = sim_paths[t-1] * np.exp((mu - 0.5 * sigma**2) * dt + sigma * np.sqrt(dt) * np.random.normal(0, 1, M_paths))
        final_prices = sim_paths[-1]
        losses = s0 - final_prices
        return np.percentile(losses, 95), np.percentile(losses, 99), sim_paths
        
    mc_var_95_single = {}
    mc_var_99_single = {}
    for t, ct in zip(tickers, clean_tickers):
        mu_s = returns_df[f'Return_{ct}'].mean()
        sigma_s = returns_df[f'Return_{ct}'].std()
        v95, v99, _ = run_mc_simulation(mu_s, sigma_s, amount)
        mc_var_95_single[t] = v95
        mc_var_99_single[t] = v99
        
    mu_port = returns_df['Port_Return'].mean()
    sigma_port = returns_df['Port_Return'].std()
    mc_var_95_port, mc_var_99_port, paths_port = run_mc_simulation(mu_port, sigma_port, amount)
    
    # 5. Maximum Historical Drawdown (Max DD)
    def calculate_max_dd_dolar(prices_series):
        roll_max = prices_series.cummax()
        dd_dolar = prices_series - roll_max
        return dd_dolar.min()
        
    max_dd_single = {}
    for t, ct in zip(tickers, clean_tickers):
        p_series = amount * (df[f'Close_{ct}'] / df[f'Close_{ct}'].iloc[0])
        max_dd_single[t] = calculate_max_dd_dolar(p_series)
        
    # Portfolio price series
    port_prices = pd.Series(0.0, index=df.index)
    for ct in clean_tickers:
        port_prices += (amount / N) * (df[f'Close_{ct}'] / df[f'Close_{ct}'].iloc[0])
        
    max_dd_port = calculate_max_dd_dolar(port_prices)
    
    # Portfolio Sharpe Ratio
    port_sharpe = returns_df['Port_Return'].mean() * 252 / port_vol if port_vol != 0 else 0.0
    
    # 6. Save Charts
    ticker_comb = "_".join(clean_tickers[:3])
    chart_name = os.path.join(output_dir, "png", f"portfolio_{ticker_comb}_monte_carlo.png")
    os.makedirs(os.path.dirname(chart_name), exist_ok=True)
    plt.figure(figsize=(10, 6))
    plt.plot(paths_port[:, :100], lw=1, alpha=0.6)
    plt.title(f"Portfolio Monte Carlo Price Projection (Equally Weighted {N} Assets)")
    plt.xlabel("Trading Day")
    plt.ylabel("Portfolio Value ($)")
    plt.axhline(amount, color='black', linestyle='--', label=f'Starting (${amount:,.0f})')
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.savefig(chart_name, dpi=300, bbox_inches='tight')
    plt.close()
    
    hist_name = os.path.join(output_dir, "png", f"portfolio_{ticker_comb}_mc_returns_histogram.png")
    os.makedirs(os.path.dirname(hist_name), exist_ok=True)
    plt.figure(figsize=(10, 6))
    plt.hist((amount - paths_port[-1]) / amount * 100, bins=50, alpha=0.75, color='royalblue', edgecolor='black')
    plt.axvline((mc_var_95_port / amount) * 100, color='orange', linestyle='--', lw=2, label=f'95% MC VaR: {(mc_var_95_port / amount) * 100:.2f}%')
    plt.axvline((mc_var_99_port / amount) * 100, color='red', linestyle='--', lw=2, label=f'99% MC VaR: {(mc_var_99_port / amount) * 100:.2f}%')
    plt.title(f"Portfolio 21-Day Monte Carlo Loss Distribution (Equally Weighted {N} Assets)")
    plt.xlabel("Portfolio Value Loss (%)")
    plt.ylabel("Trial Frequency")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.savefig(hist_name, dpi=300, bbox_inches='tight')
    plt.close()
    
    # Diversification benefit
    expected_vol = sum(weights[i] * vols[t] for i, t in enumerate(tickers))
    vol_reduction = expected_vol - port_vol
    vol_reduction_dolar = amount * vol_reduction
    
    # 7. Report Generation
    # Correlation Matrix Table
    corr_header = "| | " + " | ".join(tickers) + " |"
    corr_sep = "| :--- | " + " | ".join([":---:" for _ in tickers]) + " |"
    corr_rows = []
    for t1 in tickers:
        row = f"| **{t1}** | "
        row_vals = []
        for t2 in tickers:
            val = corr_matrix.loc[f'Return_{t1.replace(".", "_")}', f'Return_{t2.replace(".", "_")}']
            row_vals.append(f"{val:.4f}")
        row += " | ".join(row_vals) + " |"
        corr_rows.append(row)
    corr_table_str = "\n".join([corr_header, corr_sep] + corr_rows)
    
    # Scenarios Table
    header = "| Risk Metric | " + " | ".join([f"100% {t} Scenario" for t in tickers]) + " | Equally Weighted Portfolio |"
    sep = "| :--- | " + " | ".join([":---:" for _ in tickers]) + " | :---: |"
    
    vol_row = "| **Annual Volatility (%)** | " + " | ".join([f"{vols[t]*100:.2f}%" for t in tickers]) + f" | **{port_vol*100:.2f}%** |"
    vol_dolar_row = "| **Annual Volatility ($)** | " + " | ".join([f"${vols_dolar[t]:,.2f}" for t in tickers]) + f" | **${port_vol_dolar:,.2f}** |"
    var95_row = "| **Historical Daily VaR (95%)** | " + " | ".join([f"${var_95_dolar_single[t]:,.2f}" for t in tickers]) + f" | **${var_95_dolar_port:,.2f}** |"
    var99_row = "| **Historical Daily VaR (99%)** | " + " | ".join([f"${var_99_dolar_single[t]:,.2f}" for t in tickers]) + f" | **${var_99_dolar_port:,.2f}** |"
    mc95_row = "| **1-Month MC VaR (95%)** | " + " | ".join([f"${mc_var_95_single[t]:,.2f}" for t in tickers]) + f" | **${mc_var_95_port:,.2f}** |"
    mc99_row = "| **1-Month MC VaR (99%)** | " + " | ".join([f"${mc_var_99_single[t]:,.2f}" for t in tickers]) + f" | **${mc_var_99_port:,.2f}** |"
    max_dd_row = "| **Maximum Historical Drawdown** | " + " | ".join([f"${abs(max_dd_single[t]):,.2f}" for t in tickers]) + f" | **${abs(max_dd_port):,.2f}** |"
    
    compare_table_str = "\n".join([header, sep, vol_row, vol_dolar_row, var95_row, var99_row, mc95_row, mc99_row, max_dd_row])
    
    report_content = f"""# Portfolio Risk Comparison Report (Multi-Asset)

This report compares the investment scenarios of **{amount:,.2f} $** equally weighted (%{(1/N)*100:.1f} allocation each) across the stocks **{", ".join(tickers)}**.

## Key Portfolio Parameters
* **Total Investment Amount:** {amount:,.2f} $
* **Number of Assets ($N$):** {N}
* **Weight Structure:** Equally Weighted (Each asset allocated {amount/N:,.2f} $)

### Historical Return Correlation Matrix

The correlation matrix indicating the relationships between two or more stocks is shown below:

{corr_table_str}

---

## Investment Scenarios Risk Comparison Table

{compare_table_str}

---

## Portfolio Monte Carlo Simulation Charts

### Portfolio Price Projection (1-Month Horizon)
![Portfolio Monte Carlo Simulation](../png/{os.path.basename(chart_name)})

### Portfolio Value Loss Distribution and Monte Carlo VaR Thresholds
![Portfolio Loss Distribution Chart](../png/{os.path.basename(hist_name)})

---

## Diversification Effect Analysis (Diversification Benefit)

* **Volatility Reduction:** The actual volatility of the portfolio is **{vol_reduction*100:.2f}%** lower than the weighted average volatility of the individual assets. This means a risk protection/savings of **{vol_reduction_dolar:,.2f} $** on an annualized basis.
* **Maximum Drawdown Protection:** Comparing the maximum historical loss of individual stocks with the combined portfolio shows that the maximum drawdown risk is significantly limited due to diversification.

---
*Note: This report has been produced entirely using real historical data and probabilistic Monte Carlo simulations with Python. It does not constitute investment advice.*
"""
    
    os.makedirs(os.path.dirname(report_file), exist_ok=True)
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report_content)
        
    print(f"\n[OK] Portfolio comparison report successfully saved to '{report_file}'.")

if __name__ == "__main__":
    main()
