Feature: Risk Agent Orchestration and Security Audit
  As a financial analyst
  I want to securely and controllably analyze stock risk metrics via an orchestrator
  So that I can protect against fake packages and have the final say on high-risk investments.

  Scenario: Normal risk analysis with a valid ticker completes successfully
    Given a valid stock ticker like "THYAO.IS" that does not exceed risk thresholds
    When the user runs the risk agent orchestrator in non-interactive mode
    Then historical data should be fetched and saved as CSV
    And annual volatility, Sharpe ratio, and Maximum Drawdown (Max DD) metrics should be calculated
    And Monte Carlo price projection and VaR comparison steps should be completed
    And the final analysis report should be successfully generated without being overwritten.

  Scenario: Analysis fails and stops when an invalid or non-existent ticker is provided
    Given an invalid or delisted stock symbol like "XXXYZZ"
    When the user runs the risk agent orchestrator
    Then a return code of 1 should be returned during the data_fetcher step
    And the orchestrator should immediately stop and not proceed to subsequent analysis steps
    And a meaningful English error message should be displayed instead of raw tracebacks.

  Scenario: High risk triggers human-in-the-loop approval mechanism
    Given a stock like "AAPL" whose 2-year Maximum Drawdown (Max DD) is worse than -30%
    When the user runs the risk agent orchestrator in interactive mode
    Then the risk calculator should detect the high-risk condition
    And a warning showing risk details along with "Do you want to see the report? (y/n):" should appear
    And when the user enters "n" (no), the process should be safely terminated without creating a report.

  Scenario: Fake or hallucinated package detection halts orchestration (Security Check)
    Given a fake library in requirements.txt that does not exist on PyPI
    When the user runs the risk agent orchestrator with any stock symbol
    Then the PyPI security check should detect the suspicious package
    And the orchestrator should abort the process before downloading stock data
    And an English security report should be generated on disk.

  Scenario: Re-analyzing same ticker preserves old report and creates versioned copy (Versioning)
    Given an existing report file named "risk_report_THYAO_IS.md" for the stock "THYAO.IS"
    When the user runs the risk agent orchestrator for "THYAO.IS" again
    Then the existing "risk_report_THYAO_IS.md" file should not be overwritten
    And the new analysis results should be saved as "risk_report_THYAO_IS_1.md".
