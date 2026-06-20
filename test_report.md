# Test Results Report

This report contains the results of the pytest integration tests run on the actual codebase representing the Gherkin behavioral scenarios (`risk_agent.feature`).

## Test Summary
- **Report Date:** 2026-06-20 15:31:28
- **Total Tested Scenarios:** 14
- **Passed Tests:** 14
- **Failed Tests:** 0

---
> [!NOTE]
> **SUCCESS:** All behavioral scenarios defined for the project have been verified successfully on the codebase.

## Scenario Verification Table

| Behavioral Scenario | Test Class/Method | Result |
| :--- | :--- | :--- |
| Normal Risk Analysis with Valid Ticker Scenario | `test_normal_risk_analysis` | 🟢 PASSED |
| Invalid/Non-existent Ticker Scenario | `test_invalid_ticker` | 🟢 PASSED |
| High Risk Threshold Human-in-the-Loop Approval/Cancellation Scenario | `test_risk_threshold_human_in_the_loop_cancel` | 🟢 PASSED |
| test_risk_threshold_human_in_the_loop_approve | `test_risk_threshold_human_in_the_loop_approve` | 🟢 PASSED |
| Security Check Suspicious Package Detection Scenario | `test_security_check_suspicious_package` | 🟢 PASSED |
| Same Ticker Re-analysis (Versioning) Scenario | `test_same_ticker_re_analysis_versioning` | 🟢 PASSED |
| test_volatility_calculation_accuracy | `test_volatility_calculation_accuracy` | 🟢 PASSED |
| test_var_95_calculation_accuracy | `test_var_95_calculation_accuracy` | 🟢 PASSED |
| test_var_99_calculation_accuracy | `test_var_99_calculation_accuracy` | 🟢 PASSED |
| test_sharpe_ratio_calculation_accuracy | `test_sharpe_ratio_calculation_accuracy` | 🟢 PASSED |
| test_max_drawdown_calculation_accuracy | `test_max_drawdown_calculation_accuracy` | 🟢 PASSED |
| test_approval_1_deterministic_cancel | `test_approval_1_deterministic_cancel` | 🟢 PASSED |
| test_approval_3_monte_carlo_cancel | `test_approval_3_monte_carlo_cancel` | 🟢 PASSED |
| test_approval_4_comparison_cancel | `test_approval_4_comparison_cancel` | 🟢 PASSED |

## pytest Console Output Detail
```text
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-9.1.1, pluggy-1.6.0 -- D:\vartex\venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: D:\vartex
collecting ... collected 14 items

test_specs.py::test_normal_risk_analysis PASSED                          [  7%]
test_specs.py::test_invalid_ticker PASSED                                [ 14%]
test_specs.py::test_risk_threshold_human_in_the_loop_cancel PASSED       [ 21%]
test_specs.py::test_risk_threshold_human_in_the_loop_approve PASSED      [ 28%]
test_specs.py::test_security_check_suspicious_package PASSED             [ 35%]
test_specs.py::test_same_ticker_re_analysis_versioning PASSED            [ 42%]
test_specs.py::test_volatility_calculation_accuracy PASSED               [ 50%]
test_specs.py::test_var_95_calculation_accuracy PASSED                   [ 57%]
test_specs.py::test_var_99_calculation_accuracy PASSED                   [ 64%]
test_specs.py::test_sharpe_ratio_calculation_accuracy PASSED             [ 71%]
test_specs.py::test_max_drawdown_calculation_accuracy PASSED             [ 78%]
test_specs.py::test_approval_1_deterministic_cancel PASSED               [ 85%]
test_specs.py::test_approval_3_monte_carlo_cancel PASSED                 [ 92%]
test_specs.py::test_approval_4_comparison_cancel PASSED                  [100%]

============================== warnings summary ===============================
venv\Lib\site-packages\_pytest\cacheprovider.py:469
  D:\vartex\venv\Lib\site-packages\_pytest\cacheprovider.py:469: PytestCacheWarning: could not create cache path D:\vartex\.pytest_cache\v\cache\nodeids: [WinError 5] Eriim engellendi: 'D:\\vartex\\.pytest_cache\\v\\cache'
    config.cache.set("cache/nodeids", sorted(self.cached_nodeids))

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
======================= 14 passed, 1 warning in 25.98s ========================

```
