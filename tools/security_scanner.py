import subprocess
import json
from pathlib import Path


def run_checkov(folder_path: str) -> dict:
    folder = Path(folder_path)
    if not folder.exists():
        raise FileNotFoundError(f"Folder not found: {folder_path}")

    try:
        result = subprocess.run(
            ["checkov", "-d", str(folder), "-o", "json", "--quiet"],
            capture_output=True,
            text=True,
            timeout=60
        )

        output = result.stdout
        if not output.strip():
            return {
                "passed": [],
                "failed": [],
                "summary": {"error": "No output from Checkov. Is it installed? Run: pip install checkov"}
            }

        data = json.loads(output)
        if isinstance(data, list):
            data = data[0] if data else {}

        results = data.get("results", {})
        passed_checks = results.get("passed_checks", [])
        failed_checks = results.get("failed_checks", [])

        simplified_failed = []
        for check in failed_checks:
            simplified_failed.append({
                "check_id": check.get("check_id"),
                "check_name": check.get("check_type", check.get("check_id")),
                "resource": check.get("resource"),
                "file": check.get("file_path"),
                "line": check.get("file_line_range"),
                "severity": check.get("severity", "MEDIUM"),
                "guideline": check.get("guideline", "")
            })

        simplified_passed = []
        for check in passed_checks:
            simplified_passed.append({
                "check_id": check.get("check_id"),
                "resource": check.get("resource"),
            })

        summary = data.get("summary", {})

        return {
            "failed": simplified_failed,
            "passed": simplified_passed,
            "summary": {
                "total_passed": summary.get("passed", len(simplified_passed)),
                "total_failed": summary.get("failed", len(simplified_failed)),
                "resource_count": summary.get("resource_count", 0),
            }
        }

    except subprocess.TimeoutExpired:
        return {"failed": [], "passed": [], "summary": {"error": "Checkov timed out"}}
    except json.JSONDecodeError:
        return {"failed": [], "passed": [], "summary": {"error": "Could not parse Checkov output"}}
    except FileNotFoundError:
        return {"failed": [], "passed": [], "summary": {"error": "Checkov not installed. Run: pip install checkov"}}


def format_security_findings(findings: dict) -> str:
    lines = ["## Security Scan Results (Checkov)"]
    summary = findings.get("summary", {})
    lines.append(f" Passed: {summary.get('total_passed', 0)} |  Failed: {summary.get('total_failed', 0)}")
    lines.append("")

    failed = findings.get("failed", [])
    if failed:
        lines.append("### Failed Checks:")
        for f in failed:
            lines.append(f"- [{f['check_id']}] {f['check_name']}")
            lines.append(f"  Resource: {f['resource']} | File: {f['file']}")
            if f.get('guideline'):
                lines.append(f"  Guide: {f['guideline']}")
            lines.append("")
    else:
        lines.append("###  No security issues found!")

    return "\n".join(lines)