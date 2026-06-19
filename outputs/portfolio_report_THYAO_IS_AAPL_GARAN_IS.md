# Portfolio Risk Comparison Report (Multi-Asset)

This report compares the investment scenarios of **10,000.00 $** equally weighted (%20.0 allocation each) across the stocks **THYAO.IS, AAPL, GARAN.IS, MSFT, GOOGL**.

## Key Portfolio Parameters
* **Total Investment Amount:** 10,000.00 $
* **Number of Assets ($N$):** 5
* **Weight Structure:** Equally Weighted (Each asset allocated 2,000.00 $)

### Historical Return Correlation Matrix

The correlation matrix indicating the relationships between two or more stocks is shown below:

| | THYAO.IS | AAPL | GARAN.IS | MSFT | GOOGL |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **THYAO.IS** | 1.0000 | 0.0857 | 0.5429 | 0.0422 | 0.1275 |
| **AAPL** | 0.0857 | 1.0000 | 0.0833 | 0.3629 | 0.4283 |
| **GARAN.IS** | 0.5429 | 0.0833 | 1.0000 | 0.0322 | 0.1027 |
| **MSFT** | 0.0422 | 0.3629 | 0.0322 | 1.0000 | 0.3533 |
| **GOOGL** | 0.1275 | 0.4283 | 0.1027 | 0.3533 | 1.0000 |

---

## Investment Scenarios Risk Comparison Table

| Risk Metric | 100% THYAO.IS Scenario | 100% AAPL Scenario | 100% GARAN.IS Scenario | 100% MSFT Scenario | 100% GOOGL Scenario | Equally Weighted Portfolio |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Annual Volatility (%)** | 31.80% | 28.19% | 39.09% | 26.33% | 31.49% | **19.22%** |
| **Annual Volatility ($)** | $3,179.91 | $2,819.40 | $3,909.17 | $2,632.83 | $3,148.77 | **$1,922.10** |
| **Historical Daily VaR (95%)** | $258.02 | $290.25 | $347.31 | $254.45 | $275.82 | **$180.13** |
| **Historical Daily VaR (99%)** | $517.52 | $494.21 | $629.13 | $405.18 | $463.57 | **$298.84** |
| **1-Month MC VaR (95%)** | $1,434.54 | $1,162.96 | $1,648.95 | $1,272.90 | $1,163.51 | **$791.26** |
| **1-Month MC VaR (99%)** | $1,974.84 | $1,659.00 | $2,291.77 | $1,731.22 | $1,715.62 | **$1,146.88** |
| **Maximum Historical Drawdown** | $2,576.10 | $4,130.37 | $3,757.69 | $4,162.67 | $3,995.77 | **$2,138.03** |

---

## Portfolio Monte Carlo Simulation Charts

### Portfolio Price Projection (1-Month Horizon)
![Portfolio Monte Carlo Simulation](portfolio_THYAO_IS_AAPL_GARAN_IS_monte_carlo.png)

### Portfolio Value Loss Distribution and Monte Carlo VaR Thresholds
![Portfolio Loss Distribution Chart](portfolio_THYAO_IS_AAPL_GARAN_IS_mc_returns_histogram.png)

---

## Diversification Effect Analysis (Diversification Benefit)

* **Volatility Reduction:** The actual volatility of the portfolio is **12.16%** lower than the weighted average volatility of the individual assets. This means a risk protection/savings of **1,215.92 $** on an annualized basis.
* **Maximum Drawdown Protection:** Comparing the maximum historical loss of individual stocks with the combined portfolio shows that the maximum drawdown risk is significantly limited due to diversification.

---
*Note: This report has been produced entirely using real historical data and probabilistic Monte Carlo simulations with Python. It does not constitute investment advice.*
