import os
import sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def main():
    try:
        ticker = "THYAO.IS"
        report_file = None
        
        args = sys.argv[1:]
        
        # 1. Parse keyword arguments
        if "--ticker" in args:
            idx = args.index("--ticker")
            if idx + 1 < len(args):
                ticker = args[idx + 1]
        if "--report" in args:
            idx = args.index("--report")
            if idx + 1 < len(args):
                report_file = args[idx + 1]
                
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
            report_file = positionals[1]
            
        clean_ticker = ticker.replace(".", "_")
        output_dir = os.environ.get("VARTEX_OUTPUT_DIR", "outputs")
        csv_file = os.path.join(output_dir, "csv", f"{clean_ticker}_data.csv")
        
        if not report_file:
            report_file = os.path.join(output_dir, "md", f"risk_report_{clean_ticker}.md")
        
        # 1. Load data
        try:
            if os.path.exists(csv_file):
                df = pd.read_csv(csv_file, parse_dates=['Date'], index_col='Date').dropna(subset=['Close'])
            else:
                print(f"Error: {csv_file} not found.")
                sys.exit(1)
        except Exception as e:
            print(f"Error: Problem occurred during data loading (CSV read): {str(e)}")
            sys.exit(1)
            
        # 2. Risk Calculations
        try:
            # Calculate historical log returns
            df['Log_Return'] = np.log(df['Close'] / df['Close'].shift(1))
            log_returns = df['Log_Return'].dropna()
            
            if log_returns.empty:
                print(f"Error: Return data for {ticker} is empty. Analysis could not be performed.")
                sys.exit(1)
            
            # Mean and std deviation of past returns (for simulation)
            hist_mean = log_returns.mean()
            hist_std = log_returns.std()
            
            # Calculate Historical VaR (95% and 99%)
            hist_var_95 = -np.percentile(log_returns, 5)
            hist_var_99 = -np.percentile(log_returns, 1)
            
            # Monte Carlo Simulation (10,000 simulations, 1-day return projection)
            num_simulations = 10000
            simulated_returns = np.random.normal(hist_mean, hist_std, num_simulations)
            
            # Calculate Monte Carlo VaR (95% and 99%)
            mc_var_95 = -np.percentile(simulated_returns, 5)
            mc_var_99 = -np.percentile(simulated_returns, 1)
        except Exception as e:
            print(f"Error: Error occurred during historical and Monte Carlo VaR calculation phases: {str(e)}")
            sys.exit(1)
            
        # Console Output (Comparison Table)
        print("\n" + "="*70)
        print(f"  {ticker} RISK METRICS COMPARISON (1-DAY VaR)")
        print("="*70)
        print(f"{'Conf. Level':<12} | {'Historical VaR':<14} | {'Monte Carlo VaR':<15} | {'Diff (MC-Hist)':<15}")
        print("-"*70)
        print(f"{'95%':<12} | {hist_var_95*100:<13.2f}% | {mc_var_95*100:<14.2f}% | {(mc_var_95 - hist_var_95)*100:<14.2f}%")
        print(f"99%          | {hist_var_99*100:<13.2f}% | {mc_var_99*100:<14.2f}% | {(mc_var_99 - hist_var_99)*100:<14.2f}%")
        print("="*70)
        
        # 3. Visualization of distribution as a histogram
        try:
            plt.figure(figsize=(10, 6))
            plt.hist(simulated_returns * 100, bins=50, alpha=0.6, color='#4682B4', edgecolor='black', label='Simulated Returns (MC)')
            plt.axvline(-mc_var_95 * 100, color='red', linestyle='--', linewidth=2, label=f'Monte Carlo VaR 95%: -{mc_var_95*100:.2f}%')
            plt.axvline(-mc_var_99 * 100, color='darkred', linestyle=':', linewidth=2, label=f'Monte Carlo VaR 99%: -{mc_var_99*100:.2f}%')
            
            plt.title(f"{ticker} Monte Carlo 1-Day Return Distribution ({num_simulations} Trials)", fontsize=12, fontweight='bold')
            plt.xlabel("Daily Simulated Return (%)")
            plt.ylabel("Number of Days (Frequency)")
            plt.grid(True, linestyle='--', alpha=0.5)
            plt.legend()
            
            histogram_path = os.path.join(output_dir, "png", f"{clean_ticker}_mc_returns_histogram.png")
            os.makedirs(os.path.dirname(histogram_path), exist_ok=True)
            plt.savefig(histogram_path, dpi=150, bbox_inches='tight')
            plt.close()
            print(f"Simulation distribution chart saved as '{histogram_path}'.")
        except Exception as e:
            print(f"Error: Error occurred while saving distribution histogram chart: {str(e)}")
            sys.exit(1)
            
        # 4. Report Update
        try:
            # report_file is already resolved at the start of main
            if os.path.exists(report_file):
                with open(report_file, "r", encoding="utf-8") as f:
                    existing_content = f.read()
            else:
                existing_content = f"# {ticker} Stock Risk Report\n\n"
                
            addition = f"""
---

## Historical VaR vs. Monte Carlo VaR Comparison

The following table and chart compare the **Historical VaR** method using past data and the **10,000-trial Monte Carlo VaR** method over a 1-day time horizon.

### Comparison Table ({ticker})

| Confidence Level | Historical VaR | Monte Carlo VaR | Difference (MC - Historical) |
| :--- | :--- | :--- | :--- |
| **95%** | {hist_var_95*100:.2f}% | {mc_var_95*100:.2f}% | {(mc_var_95 - hist_var_95)*100:.2f}% |
| **99%** | {hist_var_99*100:.2f}% | {mc_var_99*100:.2f}% | {(mc_var_99 - hist_var_99)*100:.2f}% |

### Monte Carlo 1-Day Simulated Return Distribution ({ticker})
The distribution of returns obtained from the simulation and the Monte Carlo VaR values are shown in the chart below:

![Monte Carlo 1-Day Distribution Chart](../png/{clean_ticker}_mc_returns_histogram.png)

### Comparison Analysis Commentary
1. **Model Assumption:** While Monte Carlo VaR runs under the assumption that returns are normally distributed, Historical VaR directly incorporates skewness and heavy-tailed (kurtosis) properties present in historical data.
2. **Tail Deviations:** Real financial returns are typically fatter-tailed (extreme events happen more frequently) compared to a normal distribution. The differences between Historical VaR and Monte Carlo VaR in the comparison indicate the degree of these anomalies in the market.
"""
            
            updated_content = existing_content + addition
            os.makedirs(os.path.dirname(report_file), exist_ok=True)
            with open(report_file, "w", encoding="utf-8") as f:
                f.write(updated_content)
            print(f"Results successfully appended and updated in '{report_file}'.")
        except Exception as e:
            print(f"Error: Error occurred while adding comparison table to report: {str(e)}")
            sys.exit(1)
            
    except Exception as e:
        print(f"System Error (compare_var_methods): {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
