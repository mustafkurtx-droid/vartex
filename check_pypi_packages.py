import os
import sys
import json
import urllib.request
import urllib.error
import datetime

import time

def check_pypi_package(package_name):
    """
    Queries the specified package via the PyPI JSON API.
    """
    url = f"https://pypi.org/pypi/{package_name}/json"
    retries = 3
    delay = 1.0
    for attempt in range(retries):
        try:
            # Space out requests to PyPI
            time.sleep(0.1)
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
                
            info = data.get('info', {})
            version = info.get('version', 'Unknown')
            
            releases = data.get('releases', {})
            latest_release_files = releases.get(version, [])
            last_update = "Unknown"
            
            if latest_release_files:
                upload_time = latest_release_files[0].get('upload_time_iso_8601')
                if upload_time:
                    try:
                        dt = datetime.datetime.fromisoformat(upload_time.replace('Z', '+00:00'))
                        last_update = dt.strftime('%Y-%m-%d')
                    except Exception:
                        last_update = upload_time
                        
            vulnerabilities = data.get('vulnerabilities', [])
            vuln_count = len(vulnerabilities)
            
            return {
                "exists": True,
                "latest_version": version,
                "last_update": last_update,
                "vulnerabilities": vulnerabilities,
                "vuln_count": vuln_count
            }
            
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return {"exists": False, "error": "Not Found (404)"}
            if e.code == 429 or e.code >= 500:
                if attempt < retries - 1:
                    time.sleep(delay)
                    delay *= 2
                    continue
            return {"exists": False, "error": f"HTTP Error {e.code}"}
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(delay)
                delay *= 2
                continue
            return {"exists": False, "error": f"Connection Error: {str(e)}"}
            
    return {"exists": False, "error": "Rate limited / connection failed"}

def main():
    requirements_file = "requirements.txt"
    if not os.path.exists(requirements_file):
        print(f"Error: {requirements_file} not found.")
        sys.exit(1)
        
    # Read package list from requirements.txt
    packages = []
    with open(requirements_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            for separator in ["==", ">=", "<=", "~=", ">", "<"]:
                if separator in line:
                    line = line.split(separator)[0].strip()
                    break
            if line:
                packages.append(line)
                
    packages = sorted(list(set(packages)))
    
    results = {}
    has_issues = False
    not_found_count = 0
    vulnerable_count = 0
    
    print("\n" + "="*85)
    print("  PyPI SECURITY AND AVAILABILITY CHECK (SLOPSQUATTING CONTROL)")
    print("="*85)
    
    for pkg in packages:
        res = check_pypi_package(pkg)
        results[pkg] = res
        
        if not res["exists"]:
            err_msg = res.get("error", "")
            if "404" in err_msg:
                not_found_count += 1
                has_issues = True
                print(f"  - {pkg:<25} : [!] CRITICAL ERROR - Not found on PyPI!")
            else:
                print(f"  - {pkg:<25} : [!] WARNING - Could not verify: {err_msg}")
        elif res["vuln_count"] > 0:
            vulnerable_count += 1
            has_issues = True
            print(f"  - {pkg:<25} : [!] WARNING - {res['vuln_count']} vulnerability record(s) found!")
        else:
            # Clean package, do not print to avoid noise
            pass

    # Create English report content
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    report_content = f"""# PyPI Security and Dependency Audit Report

This report verifies the presence, last update dates, and security status of the libraries in the project's `requirements.txt` file on PyPI.

## Summary Findings
- **Audit Date:** {timestamp}
- **Total Audited Packages:** {len(packages)}
- **Number of Packages Not Found (Slopsquatting Risk):** {not_found_count}
- **Number of Vulnerable Packages:** {vulnerable_count}

"""
    if has_issues:
        report_content += """> [!WARNING]
> **WARNING:** According to audit results, security risks or potential slopsquatting/typosquatting (hallucinated package name) have been detected in some libraries. Please review the details below.

"""
    else:
        report_content += """> [!NOTE]
> **SUCCESS:** All libraries have been verified on PyPI. No known slopsquatting risk or vulnerability record was found.

"""

    report_content += """## Dependency Status Table

| Package Name | PyPI Status | Last Update | Vulnerability Status |
| :--- | :--- | :--- | :--- |
"""

    for pkg, res in results.items():
        if not res["exists"]:
            report_content += f"| **{pkg}** | `NOT FOUND (RISK)` | - | `Could not be audited` |\n"
        else:
            vuln_str = f"🔴 {res['vuln_count']} Vulnerabilities" if res['vuln_count'] > 0 else "🟢 Clean"
            report_content += f"| {pkg} | `Available` | {res['last_update']} | {vuln_str} |\n"

    report_content += "\n## Detailed Findings and Warnings\n"
    
    details_found = False
    for pkg, res in results.items():
        if not res["exists"]:
            details_found = True
            report_content += f"\n### ❌ [CRITICAL] {pkg} - Not Available on PyPI\n"
            report_content += f"**Description:** This package was not found in the PyPI package index. It is highly likely an AI hallucination (slopsquatting) or typosquatting risk. Attempting to install this package may create security vulnerabilities.\n"
        elif res["vuln_count"] > 0:
            details_found = True
            report_content += f"\n### ⚠️ [WARNING] {pkg} - {res['vuln_count']} Vulnerability Record(s)\n"
            report_content += f"**Description:** Known vulnerabilities have been detected for this package in PyPI security records.\n"
            for v in res["vulnerabilities"]:
                report_content += f"- **Vulnerability ID:** {v.get('id', 'N/A')}\n"
                report_content += f"  - **Detail:** {v.get('details', 'No description available')}\n"
                
    if not details_found:
        report_content += "\nNo suspicious activity or vulnerability has been detected.\n"

    # Write the security report into the output directory (isolation consistency
    # with the other reports/charts), not the repo root.
    output_dir = os.environ.get("VARTEX_OUTPUT_DIR", "outputs")
    report_file = os.path.join(output_dir, "md", "security_report.md")
    os.makedirs(os.path.dirname(report_file), exist_ok=True)
    try:
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(report_content)
        print(f"[OK] Security report successfully saved to '{report_file}'.")
    except Exception as e:
        print(f"Error: Could not write report file to disk: {str(e)}")
        sys.exit(1)

    # Return exit code 1 if issues were found to stop the orchestrator
    if has_issues:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()
