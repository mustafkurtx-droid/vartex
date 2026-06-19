import os
import sys
import yfinance as yf
import pandas as pd

def fetch_stock_data(ticker: str, period: str = "2y", interval: str = "1d", save_csv: bool = True) -> pd.DataFrame:
    """
    Fetches the stock data for the specified ticker using yfinance.
    Saves the data as CSV and returns it as a pandas DataFrame.
    """
    try:
        print(f"[{ticker}] Fetching data... (Period: {period}, Interval: {interval})")
        
        # Create yfinance Ticker object
        stock_ticker = yf.Ticker(ticker)
        
        # Fetch the history data
        df = stock_ticker.history(period=period, interval=interval)
        
        if df.empty:
            print(f"Error: No data found on Yahoo Finance for {ticker}.")
            return pd.DataFrame()
        
        # Remove timezone info from date index
        df.index = df.index.tz_localize(None)
        
        # Drop rows where Close price is missing
        df = df.dropna(subset=['Close'])
        
        if save_csv:
            clean_ticker = ticker.replace(".", "_")
            output_dir = os.environ.get("VARTEX_OUTPUT_DIR", "outputs")
            os.makedirs(output_dir, exist_ok=True)
            csv_filename = os.path.join(output_dir, f"{clean_ticker}_data.csv")
            df.to_csv(csv_filename)
            print(f"[{ticker}] Data saved to file '{csv_filename}'.")
            
        return df
    except Exception as e:
        print(f"Error occurred during data fetching or CSV writing: {str(e)}")
        return pd.DataFrame()

if __name__ == "__main__":
    try:
        ticker_test = "THYAO.IS"
        args = sys.argv[1:]
        
        # 1. Parse keyword arguments
        if "--ticker" in args:
            idx = args.index("--ticker")
            if idx + 1 < len(args):
                ticker_test = args[idx + 1]
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
                ticker_test = positionals[0]
                
        data = fetch_stock_data(ticker_test, period="2y", save_csv=True)
        if data.empty:
            sys.exit(1)
        
        print(f"\n--- {ticker_test} Data Summary (First 3 Days) ---")
        print(data[['Close', 'Volume']].head(3))
    except Exception as e:
        print(f"System Error (data_fetcher): {str(e)}")
        sys.exit(1)
