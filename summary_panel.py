import os
import re
import sys
import argparse
import numpy as np
import pandas as pd
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.align import Align
from rich.text import Text
from rich.box import DOUBLE

def get_color_for_metric(metric_name, value_str):
    """
    Determines metric color codes based on risk rules:
    Low risk is green, medium is yellow, critical is red.
    """
    clean_val = value_str.replace("%", "").replace("$", "").replace(",", "").strip()
    try:
        val = float(clean_val)
    except ValueError:
        return "bold yellow"
        
    m_name_lower = metric_name.lower()
    
    if "volatilite" in m_name_lower or "oynaklık" in m_name_lower or "volatility" in m_name_lower:
        if val > 50.0:
            return "bold red"
        elif val >= 30.0:
            return "bold yellow"
        else:
            return "bold green"
            
    elif "sharpe" in m_name_lower:
        if val < 0.0:
            return "bold red"
        elif val <= 0.5:
            return "bold yellow"
        else:
            return "bold green"
            
    elif "drawdown" in m_name_lower or "kayıp" in m_name_lower or "kaybi" in m_name_lower or "loss" in m_name_lower:
        abs_val = abs(val)
        if abs_val > 30.0:
            return "bold red"
        elif abs_val >= 15.0:
            return "bold yellow"
        else:
            return "bold green"
            
    elif "var" in m_name_lower:
        if "95" in m_name_lower:
            if val > 3.0:
                return "bold red"
            elif val >= 1.5:
                return "bold yellow"
            else:
                return "bold green"
        elif "99" in m_name_lower:
            if val > 5.0:
                return "bold red"
            elif val >= 3.0:
                return "bold yellow"
            else:
                return "bold green"
                
    return "bold yellow"

def parse_single_report(report_path):
    metrics = []
    if not os.path.exists(report_path):
        return metrics
        
    with open(report_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    pattern = r"\|\s*\*\*?(.*?)\*\*?\s*\|\s*([^|]*?)\s*\|\s*([^|]*?)\s*\|"
    matches = re.findall(pattern, content)
    
    for match in matches:
        metric_name = match[0].strip()
        value = match[1].strip()
        desc = match[2].strip()
        
        if "Risk Metriği" in metric_name or "Risk Metric" in metric_name or "Calculated" in value:
            continue
            
        metrics.append((metric_name, value, desc))
        
    return metrics

def parse_portfolio_report(report_path):
    if not os.path.exists(report_path):
        return None, [], None
        
    with open(report_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    lines = content.splitlines()
    
    headers = []
    rows = []
    in_table = False
    
    for line in lines:
        if "|" in line:
            if ":---" in line or "---:" in line:
                in_table = True
                continue
            parts = [p.strip() for p in line.split("|")[1:-1]]
            if not parts:
                continue
            if "Risk Metriği" in parts[0] or "Risk Metric" in parts[0]:
                headers = parts
                in_table = True
            elif in_table:
                # Stop if another table starts
                if parts[0] == "" or "thyao" in parts[0].lower() or "aran" in parts[0].lower() or "aapl" in parts[0].lower():
                    in_table = False
                    continue
                rows.append(parts)
        elif in_table and line.strip() == "":
            in_table = False
            
    return headers, rows, content

def show_single_panel(ticker, report_path):
    console = Console()
    metrics = parse_single_report(report_path)
    
    if not metrics:
        console.print(f"[bold red]Error:[/] File '{report_path}' could not be read or has an invalid format.")
        return
        
    filtered_metrics = []
    for m, v, d in metrics:
        clean_m = m.replace("**", "").replace("*", "")
        m_lower = clean_m.lower()
        if any(keyword in m_lower for keyword in ["volatilite", "oynaklık", "volatility", "var", "sharpe", "drawdown", "kayıp", "kaybi", "loss"]):
            filtered_metrics.append((clean_m, v, d))
            
    table = Table(show_header=True, header_style="bold magenta", box=DOUBLE)
    table.add_column("Risk Metric", style="cyan", width=30)
    table.add_column("Value", justify="right", width=15)
    table.add_column("Description", style="green", width=50)
    
    for m, v, d in filtered_metrics:
        color = get_color_for_metric(m, v)
        table.add_row(m, Text(v, style=color), d)
        
    panel = Panel(
        Align.center(table),
        title=f"[bold green] VARTEX - [{ticker}]\nRisk Analiz Özeti[/]",
        subtitle=f"[bold blue]Report Location: {os.path.abspath(report_path)}[/]",
        border_style="green",
        expand=False
    )
    
    console.print("\n")
    console.print(panel)
    console.print("\n")

def show_portfolio_panel(report_path):
    console = Console()
    headers, rows, content = parse_portfolio_report(report_path)
    
    if not headers or not rows:
        console.print(f"[bold red]Error:[/] Portfolio report file '{report_path}' could not be read.")
        return
        
    # 1. Create Table
    table = Table(show_header=True, header_style="bold magenta", box=DOUBLE)
    for i, h in enumerate(headers):
        style = "cyan" if i == 0 else ("bold green" if i == len(headers) - 1 else "yellow")
        table.add_column(h.replace("**", "").replace("*", ""), style=style, justify="left" if i == 0 else "right")
        
    for row in rows:
        clean_row = [r.replace("**", "").replace("*", "") for r in row]
        table.add_row(*clean_row)
        
    # 2. Diversification Benefit Panel
    vol_reduction_pct = "0.00"
    vol_reduction_dolar = "0.00"
    
    # Try parsing both Turkish and English formats
    pct_match = re.search(r"\*\*([0-9.]+)%\*\*\s*lower", content, re.IGNORECASE)
    if pct_match:
        vol_reduction_pct = pct_match.group(1).strip()
    else:
        pct_match2 = re.search(r"\*\*%\s*([0-9.]+)\*\*\s*risk düşüşü", content, re.IGNORECASE)
        if pct_match2:
            vol_reduction_pct = pct_match2.group(1).strip()
        else:
            pct_match3 = re.search(r"ortalamasından\s*\*\*%\s*([0-9.]+)\*\*", content, re.IGNORECASE)
            if pct_match3:
                vol_reduction_pct = pct_match3.group(1).strip()
                
    dolar_match = re.search(r"savings\s*of\s*\*\*([0-9,.]+)\s*\$?\*\*", content, re.IGNORECASE)
    if dolar_match:
        vol_reduction_dolar = dolar_match.group(1).strip()
    else:
        dolar_match2 = re.search(r"\*\*\s*([0-9,.]+)\s*\$\*\*\s*tasarruf", content, re.IGNORECASE)
        if dolar_match2:
            vol_reduction_dolar = dolar_match2.group(1).strip()
        else:
            dolar_match3 = re.search(r"bazda\s*\*\*\s*([0-9,.]+)\s*\$\*\*", content, re.IGNORECASE)
            if dolar_match3:
                vol_reduction_dolar = dolar_match3.group(1).strip()
            
    benefit_panel = Panel(
        Text(f"Portfolio risk reduced by {vol_reduction_pct}% due to diversification!\nAnnualized Risk Savings: {vol_reduction_dolar} $", style="bold green", justify="center"),
        title="[bold green] Diversification Benefit[/]",
        border_style="green",
        expand=False
    )
    
    # 3. Correlation Matrix Summary
    tickers = [h.replace("**", "").replace("*", "").replace("%100 ", "").replace(" Scenario", "").replace(" Senaryosu", "").strip() for h in headers[1:-1]]
    
    min_corr = 1.0
    max_corr = -1.0
    min_pair = ("", "")
    max_pair = ("", "")
    
    for row_text in content.splitlines():
        if "|" in row_text and any(t in row_text for t in tickers):
            parts = [p.strip() for p in row_text.split("|")[1:-1]]
            if not parts:
                continue
            t1 = parts[0].replace("**", "").replace("*", "").strip()
            if t1 not in tickers:
                continue
            for j, val_str in enumerate(parts[1:]):
                if j < len(tickers):
                    t2 = tickers[j]
                    if t1 != t2:
                        try:
                            val = float(val_str.strip())
                            if val < min_corr:
                                min_corr = val
                                min_pair = (t1, t2)
                            if val > max_corr:
                                max_corr = val
                                max_pair = (t1, t2)
                        except ValueError:
                            pass
                            
    corr_summary_text = ""
    if min_pair[0] and max_pair[0]:
        corr_summary_text = (
            f"[bold cyan]Lowest Correlation (Best Diversification):[/] {min_pair[0]} - {min_pair[1]} ({min_corr:.4f})\n"
            f"[bold magenta]Highest Correlation (Lowest Diversification):[/] {max_pair[0]} - {max_pair[1]} ({max_corr:.4f})"
        )
        
    corr_panel = Panel(
        Text(corr_summary_text, style="cyan"),
        title="[bold cyan] Correlation Matrix Summary[/]",
        border_style="cyan",
        expand=False
    )
    
    # 4. Layout
    layout_table = Table.grid(expand=True)
    layout_table.add_row(table)
    layout_table.add_row("")
    
    grid = Table.grid(expand=True)
    grid.add_column(width=55)
    grid.add_column(width=55)
    grid.add_row(benefit_panel, corr_panel)
    
    layout_table.add_row(grid)
    
    N = len(tickers)
    panel = Panel(
        Align.center(layout_table),
        title=f"[bold green] VARTEX - {N}-Asset Portfolio Summary[/]",
        subtitle=f"[bold blue]Report Location: {os.path.abspath(report_path)}[/]",
        border_style="green",
        expand=False
    )
    
    console.print("\n")
    console.print(panel)
    console.print("\n")

def main():
    parser = argparse.ArgumentParser(description="Rich Terminal Summary Panel")
    parser.add_argument("--type", type=str, choices=["single", "portfolio"], required=True)
    parser.add_argument("--ticker", type=str)
    parser.add_argument("--report", type=str, required=True)
    
    args = parser.parse_args()
    
    if args.type == "single":
        ticker = args.ticker if args.ticker else "Stock"
        show_single_panel(ticker, args.report)
    elif args.type == "portfolio":
        show_portfolio_panel(args.report)

if __name__ == "__main__":
    main()
