import os
import sys
import subprocess
import datetime

def main():
    print(">>> Starting integration tests...")
    
    # Locate pytest executable in venv
    pytest_bin = os.path.join("venv", "Scripts", "pytest.exe")
    if not os.path.exists(pytest_bin):
        pytest_bin = os.path.join("venv", "Scripts", "pytest")
    if not os.path.exists(pytest_bin):
        pytest_bin = "pytest"
        
    # Run tests in verbose mode and capture output
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "test_specs.py", "-v"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="ignore"
    )
    
    output = result.stdout
    stderr_output = result.stderr
    
    # Print outputs to console
    print(output)
    if stderr_output:
        print(stderr_output)
        
    # Parse lines to analyze test states
    lines = output.splitlines()
    test_results = []
    
    # Dictionary mapping pytest methods to English Gherkin scenario descriptions
    test_names_en = {
        "test_normal_risk_analysis": "Normal Risk Analysis with Valid Ticker Scenario",
        "test_invalid_ticker": "Invalid/Non-existent Ticker Scenario",
        "test_risk_threshold_human_in_the_loop_cancel": "High Risk Threshold Human-in-the-Loop Approval/Cancellation Scenario",
        "test_security_check_suspicious_package": "Security Check Suspicious Package Detection Scenario",
        "test_same_ticker_re_analysis_versioning": "Same Ticker Re-analysis (Versioning) Scenario"
    }
    
    passed_count = 0
    failed_count = 0
    
    for line in lines:
        if "test_specs.py::" in line:
            # Extract method name
            parts = line.split("::")
            test_name = parts[1].split(" ")[0].strip()
            
            if "PASSED" in line:
                status_clean = "🟢 PASSED"
                passed_count += 1
            elif "FAILED" in line:
                status_clean = "🔴 FAILED"
                failed_count += 1
            else:
                status_clean = "🟡 UNKNOWN"
                
            test_desc = test_names_en.get(test_name, test_name)
            
            test_results.append({
                "name": test_desc,
                "status": status_clean,
                "raw_name": test_name
            })
            
    # English Report Generation
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    total_tests = passed_count + failed_count
    
    report_content = f"""# Test Results Report

This report contains the results of the pytest integration tests run on the actual codebase representing the Gherkin behavioral scenarios (`risk_agent.feature`).

## Test Summary
- **Report Date:** {timestamp}
- **Total Tested Scenarios:** {total_tests}
- **Passed Tests:** {passed_count}
- **Failed Tests:** {failed_count}

"""
    if failed_count > 0:
        report_content += """---\n> [!WARNING]\n> **WARNING:** Some behavioral scenarios failed during verification. Please review the details below.\n\n"""
    else:
        report_content += """---\n> [!NOTE]\n> **SUCCESS:** All behavioral scenarios defined for the project have been verified successfully on the codebase.\n\n"""

    report_content += """## Scenario Verification Table

| Behavioral Scenario | Test Class/Method | Result |
| :--- | :--- | :--- |
"""

    for res in test_results:
        report_content += f"| {res['name']} | `{res['raw_name']}` | {res['status']} |\n"

    report_content += "\n## pytest Console Output Detail\n"
    report_content += "```text\n" + output + "\n```\n"
    
    report_file = "test_report.md"
    try:
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(report_content)
        print(f"\n[OK] Test report successfully saved to '{report_file}'.")
    except Exception as e:
        print(f"Error: Could not write test report: {str(e)}")
        sys.exit(1)
        
    if failed_count > 0:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()
