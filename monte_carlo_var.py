import os
import sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from data_fetcher import fetch_stock_data

def run_monte_carlo_simulation(ticker: str, num_simulations: int = 10000, horizon_days: int = 21) -> dict:
    """
    Performs Monte Carlo simulation using Geometric Brownian Motion (GBM).
    Plots price paths and calculates Monte Carlo VaR values for 1-day and horizon_days ends.
    """
    try:
        clean_ticker = ticker.replace(".", "_")
        output_dir = os.environ.get("VARTEX_OUTPUT_DIR", "outputs")
        csv_file = os.path.join(output_dir, f"{clean_ticker}_data.csv")
        
        # 1. Data Loading
        try:
            if os.path.exists(csv_file):
                df = pd.read_csv(csv_file, parse_dates=['Date'], index_col='Date').dropna(subset=['Close'])
            else:
                df = fetch_stock_data(ticker, period="2y", save_csv=True)
        except Exception as e:
            print(f"Error: Error occurred during simulation data loading phase: {str(e)}")
            return {}
            
        if df.empty:
            print(f"Error: No data found for {ticker} simulation.")
            return {}
            
        # 2. Statistical Parameter Calculation
        try:
            # Calculate daily log returns
            df['Log_Return'] = np.log(df['Close'] / df['Close'].shift(1))
            log_returns = df['Log_Return'].dropna()
            
            if log_returns.empty:
                print(f"Error: Insufficient return data for {ticker}.")
                return {}
                
            mu = log_returns.mean()          # Daily mean log return (drift)
            sigma = log_returns.std()        # Daily volatility (std)
            last_price = df['Close'].iloc[-1] # Last observed price (S0)
        except Exception as e:
            print(f"Error: Mathematical error occurred while calculating simulation parameters: {str(e)}")
            return {}
        
        # 3. GBM Simulation Phase
        try:
            print(f"\n[Monte Carlo Parameters - {ticker}]:")
            print(f"  - Last Price (S0)           : {last_price:.2f}")
            print(f"  - Daily Mean (Drift)        : {mu:.6f}")
            print(f"  - Daily Std Deviation       : {sigma:.6f}")
            print(f"  - Simulation Path Count     : {num_simulations}")
            print(f"  - Time Horizon (Trading Days): {horizon_days}")
            
            # Create price matrix
            price_matrix = np.zeros((horizon_days + 1, num_simulations))
            price_matrix[0] = last_price
            
            # GBM Formula drift part
            drift = mu - 0.5 * (sigma ** 2)
            
            # Run simulation
            for t in range(1, horizon_days + 1):
                Z = np.random.standard_normal(num_simulations)
                price_matrix[t] = price_matrix[t - 1] * np.exp(drift + sigma * Z)
        except Exception as e:
            print(f"Error: Error occurred while calculating simulation matrix (GBM): {str(e)}")
            return {}
            
        # 4. VaR Calculation and Plotting
        try:
            # 1-Day Simulated Returns
            simulated_daily_returns = (price_matrix[1] - last_price) / last_price
            mc_var_95_1d = -np.percentile(simulated_daily_returns, 5)
            mc_var_99_1d = -np.percentile(simulated_daily_returns, 1)
            
            # Horizon Simulated Returns
            simulated_horizon_returns = (price_matrix[-1] - last_price) / last_price
            mc_var_95_horizon = -np.percentile(simulated_horizon_returns, 5)
            mc_var_99_horizon = -np.percentile(simulated_horizon_returns, 1)
            
            # Plot simulation paths
            plt.figure(figsize=(12, 6))
            
            # Plot first 100 paths
            plt.plot(price_matrix[:, :100], color='gray', alpha=0.15)
            
            # Calculate statistical summary paths
            time_steps = np.arange(horizon_days + 1)
            median_path = np.median(price_matrix, axis=1)
            p95_path = np.percentile(price_matrix, 95, axis=1) 
            p5_path = np.percentile(price_matrix, 5, axis=1)   
            
            # Add lines to chart
            plt.plot(time_steps, median_path, color='#002244', linewidth=2.5, label='Median (Expected Price Path)')
            plt.plot(time_steps, p95_path, color='#228B22', linewidth=2, linestyle='--', label='95% Best Case Scenario Boundary')
            plt.plot(time_steps, p5_path, color='#E30A17', linewidth=2, linestyle='--', label='5% Worst Case Scenario Boundary (VaR)')
            
            plt.title(f"{ticker} Monte Carlo Price Projection ({num_simulations} Simulations)", fontsize=13, fontweight='bold')
            plt.xlabel("Trading Day", fontsize=11)
            plt.ylabel("Price", fontsize=11)
            plt.grid(True, linestyle='--', alpha=0.5)
            plt.legend()
            
            chart_path = os.path.join(output_dir, f"{clean_ticker}_monte_carlo.png")
            plt.savefig(chart_path, dpi=300, bbox_inches='tight')
            plt.close()
            print(f"Simulation chart saved as '{chart_path}'.")
        except Exception as e:
            print(f"Error: Error occurred during risk metrics calculation or chart plotting: {str(e)}")
            return {}
            
        return {
            "Ticker": ticker,
            "Last_Price": last_price,
            "Simulations": num_simulations,
            "Horizon": horizon_days,
            "MC_VaR_95_1d": mc_var_95_1d,
            "MC_VaR_99_1d": mc_var_99_1d,
            "MC_VaR_95_horizon": mc_var_95_horizon,
            "MC_VaR_99_horizon": mc_var_99_horizon,
            "Chart_Path": chart_path
        }
    except Exception as e:
        print(f"System Error (monte_carlo_var): {str(e)}")
        return {}

if __name__ == "__main__":
    try:
        ticker_symbol = "THYAO.IS"
        args = sys.argv[1:]
        
        # 1. Parse keyword arguments
        if "--ticker" in args:
            idx = args.index("--ticker")
            if idx + 1 < len(args):
                ticker_symbol = args[idx + 1]
        else:
            # 2. Extract positional arguments
            positionals = []
            i = 0
            while i < len(args):
                arg = args[i]
                if arg.startswith("-"):
                    i += 1
                else:
                    positionals.append(arg)
                    i += 1
            if len(positionals) > 0:
                ticker_symbol = positionals[0]
                
        results = run_monte_carlo_simulation(ticker_symbol, num_simulations=10000, horizon_days=21)
        
        if not results:
            sys.exit(1)
            
        print("\n" + "="*60)
        print(f"  {results['Ticker']} MONTE CARLO RISK ANALYSIS RESULTS")
        print("="*60)
        print(f"Last Stock Price (S0)                : {results['Last_Price']:.2f}")
        print(f"Time Horizon                         : {results['Horizon']} Trading Days (1 Month)")
        print("-"*60)
        print("1-DAY MONTE CARLO VaR:")
        print(f"  - 95% Confidence Level VaR         : {results['MC_VaR_95_1d']*100:.2f}%")
        print(f"  - 99% Confidence Level VaR         : {results['MC_VaR_99_1d']*100:.2f}%")
        print("-"*60)
        print(f"{results['Horizon']}-DAY MONTE CARLO VaR:")
        print(f"  - 95% Confidence Level VaR         : {results['MC_VaR_95_horizon']*100:.2f}%")
        print(f"  - 99% Confidence Level VaR         : {results['MC_VaR_99_horizon']*100:.2f}%")
        print("="*60)
    except Exception as e:
        print(f"System Runtime Error (monte_carlo_var main): {str(e)}")
        sys.exit(1)
