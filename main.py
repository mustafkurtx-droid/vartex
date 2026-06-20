import os
import sys
import shutil
import subprocess

def run_security_check():
    # Test-only opt-in bypass (default off). The dedicated security test does
    # NOT set this, so the real PyPI audit is still exercised there.
    if os.environ.get("VARTEX_SKIP_SECURITY") == "1":
        print(">>> Security check skipped (VARTEX_SKIP_SECURITY=1).")
        return
    print(">>> Running security check on requirements.txt...")
    result = subprocess.run(
        [sys.executable, "check_pypi_packages.py"],
        capture_output=False,
        text=True
    )
    if result.returncode != 0:
        print("[-] Security check failed! Aborting execution.")
        sys.exit(1)
    print("[+] Security check passed.")

def get_versioned_report_path(ticker, output_dir):
    clean_ticker = ticker.replace(".", "_")
    base_name = os.path.join(output_dir, f"risk_report_{clean_ticker}")
    
    # Check if base file exists
    report_path = f"{base_name}.md"
    if not os.path.exists(report_path):
        return report_path
        
    # Find next version
    version = 1
    while True:
        report_path = f"{base_name}_{version}.md"
        if not os.path.exists(report_path):
            return report_path
        version += 1

def prompt_user(message, no_interactive=False):
    if no_interactive:
        return True
    
    # Check if running in an interactive terminal
    is_interactive = sys.stdin.isatty() or os.environ.get("FORCE_INTERACTIVE") == "1"
    if not is_interactive:
        return True
        
    while True:
        try:
            choice = input(f"{message} (y/n): ").strip().lower()
            if choice == 'y':
                return True
            elif choice == 'n':
                return False
            else:
                print("Invalid input. Please type 'y' or 'n'.")
        except (EOFError, KeyboardInterrupt):
            print("\nProcess cancelled.")
            return False

def run_single_stock(ticker, no_interactive, output_dir, input_csv=None):
    print(f"\n==========================================")
    print(f"  Analyzing Ticker: {ticker}")
    print(f"==========================================")

    # 1. Fetch stock data (or use a provided CSV in test mode, skipping yfinance)
    if input_csv:
        clean_ticker = ticker.replace(".", "_")
        dest = os.path.join(output_dir, f"{clean_ticker}_data.csv")
        print(f">>> Test mode: using provided CSV '{input_csv}' (skipping network fetch)...")
        try:
            shutil.copy2(input_csv, dest)
        except Exception as e:
            print(f"[-] Error: Could not load provided --input-csv '{input_csv}': {str(e)}")
            sys.exit(1)
    else:
        print(">>> Fetching stock data...")
        result = subprocess.run(
            [sys.executable, "data_fetcher.py", ticker],
            capture_output=False,
            text=True
        )
        if result.returncode != 0:
            print(f"[-] Error: Data fetching failed for ticker '{ticker}'. Please verify the stock symbol.")
            sys.exit(1)
        
    # 2. Prompt for deterministic risk analysis
    if not prompt_user("[?] Stock data fetched successfully. Proceed to deterministic risk analysis?", no_interactive):
        print("[-] Process cancelled by user.")
        sys.exit(0)
        
    # Generate the versioned report path
    report_path = get_versioned_report_path(ticker, output_dir)
    
    # 3. Run deterministic risk analysis
    print(">>> Running deterministic risk analysis...")
    cmd = [sys.executable, "calculate_and_report.py", ticker, "--report", report_path]
    if no_interactive:
        cmd.append("--no-interactive")
        
    result = subprocess.run(cmd, capture_output=False, text=True)
    if result.returncode == 2:
        print("[-] Analysis stopped or rejected by user due to high risk.")
        sys.exit(2)
    elif result.returncode != 0:
        print("[-] Error: Deterministic risk analysis failed.")
        sys.exit(1)
        
    # 4. Prompt for Monte Carlo simulation
    if not prompt_user("[?] Deterministic risk analysis report created. Proceed to Monte Carlo price simulation?", no_interactive):
        print("[-] Process cancelled by user.")
        sys.exit(0)
        
    # 5. Run Monte Carlo simulation
    print(">>> Running Monte Carlo price simulation...")
    result = subprocess.run(
        [sys.executable, "monte_carlo_var.py", ticker],
        capture_output=False,
        text=True
    )
    if result.returncode != 0:
        print("[-] Error: Monte Carlo simulation failed.")
        sys.exit(1)
        
    # 6. Prompt for comparative VaR analysis
    if not prompt_user("[?] Monte Carlo price projection completed. Proceed to comparative VaR methodology analysis?", no_interactive):
        print("[-] Process cancelled by user.")
        sys.exit(0)
        
    # 7. Run comparative VaR methodology analysis
    print(">>> Running comparative VaR methodology analysis...")
    result = subprocess.run(
        [sys.executable, "compare_var_methods.py", ticker, "--report", report_path],
        capture_output=False,
        text=True
    )
    if result.returncode != 0:
        print("[-] Error: Comparative VaR analysis failed.")
        sys.exit(1)
        
    # 8. Show summary panel
    print(">>> Rendering summary panel...")
    subprocess.run(
        [sys.executable, "summary_panel.py", "--type", "single", "--ticker", ticker, "--report", report_path]
    )

def run_portfolio_mode(tickers, amount, no_interactive, output_dir):
    print(f"\n==========================================")
    print(f"  Portfolio Mode: {len(tickers)} Assets | Amount: {amount}")
    print(f"==========================================")
    
    # Sequentially prompt and analyze each stock
    for ticker in tickers:
        print(f"\n>>> Verifying and analyzing asset: {ticker}")
        
        # 1. Fetch stock data
        result = subprocess.run(
            [sys.executable, "data_fetcher.py", ticker],
            capture_output=False,
            text=True
        )
        if result.returncode != 0:
            print(f"[-] Error: Data fetching failed for ticker '{ticker}'. Aborting portfolio analysis.")
            sys.exit(1)
            
        # 2. Prompt for deterministic risk analysis
        if not prompt_user(f"[?] Stock data fetched successfully for {ticker}. Proceed to deterministic risk analysis?", no_interactive):
            print("[-] Process cancelled by user.")
            sys.exit(0)
            
        report_path = get_versioned_report_path(ticker, output_dir)
        
        # 3. Run deterministic risk analysis
        cmd = [sys.executable, "calculate_and_report.py", ticker, "--report", report_path]
        if no_interactive:
            cmd.append("--no-interactive")
            
        result = subprocess.run(cmd, capture_output=False, text=True)
        if result.returncode == 2:
            print(f"[-] Analysis stopped/rejected for {ticker} due to high risk.")
            sys.exit(2)
        elif result.returncode != 0:
            print(f"[-] Error: Deterministic risk analysis failed for {ticker}.")
            sys.exit(1)
            
        # 4. Prompt for Monte Carlo simulation
        if not prompt_user(f"[?] Deterministic risk analysis report created for {ticker}. Proceed to Monte Carlo price simulation?", no_interactive):
            print("[-] Process cancelled by user.")
            sys.exit(0)
            
        # 5. Run Monte Carlo simulation
        result = subprocess.run(
            [sys.executable, "monte_carlo_var.py", ticker],
            capture_output=False,
            text=True
        )
        if result.returncode != 0:
            print(f"[-] Error: Monte Carlo simulation failed for {ticker}.")
            sys.exit(1)
            
        # 6. Prompt for comparative VaR analysis
        if not prompt_user(f"[?] Monte Carlo price projection completed for {ticker}. Proceed to comparative VaR methodology analysis?", no_interactive):
            print("[-] Process cancelled by user.")
            sys.exit(0)
            
        # 7. Run comparative VaR methodology analysis
        result = subprocess.run(
            [sys.executable, "compare_var_methods.py", ticker, "--report", report_path],
            capture_output=False,
            text=True
        )
        if result.returncode != 0:
            print(f"[-] Error: Comparative VaR analysis failed for {ticker}.")
            sys.exit(1)

    # All tickers analyzed, prompt for portfolio-level analysis
    tickers_str = ", ".join(tickers)
    if not prompt_user(f"[?] Selected stocks ({tickers_str}) analyzed successfully. Proceed to joint portfolio risk scenarios analysis?", no_interactive):
        print("[-] Process cancelled by user before joint portfolio analysis.")
        sys.exit(0)
        
    # Run portfolio analysis
    print("\n>>> Running joint portfolio risk scenarios analysis...")
    clean_tickers = [t.replace(".", "_") for t in tickers]
    ticker_comb = "_".join(clean_tickers[:3])
    
    # Find next versioned portfolio report path
    base_portfolio_report = os.path.join(output_dir, f"portfolio_report_{ticker_comb}")
    portfolio_report_path = f"{base_portfolio_report}.md"
    if os.path.exists(portfolio_report_path):
        version = 1
        while True:
            portfolio_report_path = f"{base_portfolio_report}_{version}.md"
            if not os.path.exists(portfolio_report_path):
                break
            version += 1
            
    cmd = [
        sys.executable, "portfolio_analysis.py",
        "--tickers", *tickers,
        "--amount", str(amount),
        "--report", portfolio_report_path
    ]
    result = subprocess.run(cmd, capture_output=False, text=True)
    if result.returncode != 0:
        print("[-] Error: Portfolio risk analysis failed.")
        sys.exit(1)
        
    # Render portfolio summary panel
    print(">>> Rendering portfolio summary panel...")
    subprocess.run(
        [sys.executable, "summary_panel.py", "--type", "portfolio", "--report", portfolio_report_path]
    )

def main():
    # Setup output directory
    output_dir = os.environ.get("VARTEX_OUTPUT_DIR", "outputs")
    os.makedirs(output_dir, exist_ok=True)
    
    # Parse arguments
    args = sys.argv[1:]
    if not args:
        print("Usage:")
        print("  Single Stock: python main.py <TICKER> [--no-interactive]")
        print("  Portfolio:    python main.py --portfolio <TICKER1> <TICKER2>... --amount <AMOUNT> [--no-interactive]")
        sys.exit(1)
        
    no_interactive = "--no-interactive" in args

    # Optional test-mode CSV: bypasses yfinance by feeding a fixed dataset.
    input_csv = None
    if "--input-csv" in args:
        idx = args.index("--input-csv")
        if idx + 1 < len(args):
            input_csv = args[idx + 1]
        else:
            print("Error: --input-csv requires a file path.")
            sys.exit(1)

    # Clean flags (and --input-csv's value) from the list to ease manual parsing
    args_clean = []
    skip_next = False
    for a in args:
        if skip_next:
            skip_next = False
            continue
        if a == "--no-interactive":
            continue
        if a == "--input-csv":
            skip_next = True
            continue
        args_clean.append(a)

    # 1. Run security check first
    run_security_check()
    
    if "--portfolio" in args_clean:
        try:
            port_idx = args_clean.index("--portfolio")
            if "--amount" not in args_clean:
                print("Error: Portfolio mode requires --amount argument.")
                sys.exit(1)
            amount_idx = args_clean.index("--amount")
            
            # Extract tickers
            if port_idx < amount_idx:
                tickers = args_clean[port_idx + 1 : amount_idx]
                amount_str = args_clean[amount_idx + 1]
            else:
                tickers = args_clean[port_idx + 1 :]
                amount_str = args_clean[amount_idx + 1 : port_idx][0]
                
            if not tickers:
                print("Error: No tickers specified after --portfolio.")
                sys.exit(1)
                
            amount = float(amount_str)
        except Exception as e:
            print(f"Error parsing portfolio arguments: {str(e)}")
            print("Usage: python main.py --portfolio <T1> <T2>... --amount <AMOUNT> [--no-interactive]")
            sys.exit(1)
            
        run_portfolio_mode(tickers, amount, no_interactive, output_dir)
    else:
        # Single stock mode
        ticker = args_clean[0]
        if ticker.startswith("-"):
            print(f"Error: Unknown argument '{ticker}'.")
            sys.exit(1)
        run_single_stock(ticker, no_interactive, output_dir, input_csv)

if __name__ == "__main__":
    main()
