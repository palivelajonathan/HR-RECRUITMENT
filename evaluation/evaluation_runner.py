"""
Master Evaluation Harness CLI Runner.

CAPABL Track 6 Requirement:
- Runs individual or comprehensive evaluation suites: retrieval, rag, tools, agent, security.
- Aggregates measured precision, recall, groundedness, tool fidelity, and adversarial defense rates.
- Never fabricates numbers: outputs exact empirical metrics to console and JSON reports.

Usage:
    python -m evaluation.evaluation_runner --suite retrieval
    python -m evaluation.evaluation_runner --suite rag
    python -m evaluation.evaluation_runner --suite tools
    python -m evaluation.evaluation_runner --suite agent
    python -m evaluation.evaluation_runner --suite security
    python -m evaluation.evaluation_runner --all
    python -m evaluation.evaluation_runner --all --output evaluation/reports/M7_BASELINE.json
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List

from evaluation.runners.retrieval_runner import run_retrieval_evaluation
from evaluation.runners.rag_runner import run_rag_evaluation
from evaluation.runners.tool_runner import run_tool_evaluation
from evaluation.runners.agent_runner import run_agent_evaluation
from evaluation.runners.security_runner import run_security_evaluation


def run_suites(selected_suites: List[str]) -> Dict[str, Any]:
    """
    Executes selected evaluation suites and compiles the consolidated report.
    """
    suite_map = {
        "retrieval": run_retrieval_evaluation,
        "rag": run_rag_evaluation,
        "tools": run_tool_evaluation,
        "agent": run_agent_evaluation,
        "security": run_security_evaluation,
    }

    results: Dict[str, Any] = {}
    total_cases = 0
    total_passed = 0
    total_failed = 0

    print(f"\n==================================================================")
    print(f"       CAPABL TRACK 6 — SYSTEM EVALUATION HARNESS (M7)             ")
    print(f"==================================================================")
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print(f"Suites Selected: {', '.join(selected_suites)}\n")

    for suite_name in selected_suites:
        runner_fn = suite_map.get(suite_name)
        if not runner_fn:
            print(f"[WARN] Unknown suite '{suite_name}', skipping.")
            continue

        print(f"--- Running Suite: {suite_name.upper()} ---")
        try:
            suite_res = runner_fn()
            results[suite_name] = suite_res
            cases = suite_res.get("cases", 0)
            passed = suite_res.get("passed", 0)
            failed = suite_res.get("failed", 0)
            status = suite_res.get("status", "UNKNOWN")

            total_cases += cases
            total_passed += passed
            total_failed += failed

            print(f"[{status}] {suite_name.upper()}: {passed}/{cases} passed ({failed} failed)")
            print(f"Metrics: {json.dumps(suite_res.get('metrics', {}), indent=2)}")
        except Exception as exc:
            print(f"[FAIL] Error running suite '{suite_name}': {exc}")
            results[suite_name] = {
                "suite": suite_name,
                "status": "ERROR",
                "error": str(exc),
                "cases": 0,
                "passed": 0,
                "failed": 0,
                "metrics": {},
            }
            total_failed += 1

    overall_status = "PASS" if total_failed == 0 and total_cases > 0 else "FAIL"

    consolidated_report = {
        "title": "CAPABL Track 6 System Evaluation Baseline",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": overall_status,
        "total_cases": total_cases,
        "total_passed": total_passed,
        "total_failed": total_failed,
        "suites": results,
    }

    print(f"\n==================================================================")
    print(f"       EVALUATION SUMMARY: [{overall_status}]")
    print(f"       Total Cases: {total_cases} | Passed: {total_passed} | Failed: {total_failed}")
    print(f"==================================================================\n")

    return consolidated_report


def main():
    parser = argparse.ArgumentParser(description="CAPABL Track 6 Evaluation Harness Runner")
    parser.add_argument(
        "--suite",
        type=str,
        choices=["retrieval", "rag", "tools", "agent", "security"],
        help="Run a specific evaluation suite.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run all 5 evaluation suites (retrieval, rag, tools, agent, security).",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="evaluation/reports/M7_BASELINE.json",
        help="Output JSON report filepath.",
    )

    args = parser.parse_args()

    if args.all or not args.suite:
        suites_to_run = ["retrieval", "rag", "tools", "agent", "security"]
    else:
        suites_to_run = [args.suite]

    report = run_suites(suites_to_run)

    # Save report
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"Evaluation report exported to: {out_path.resolve()}")

    if report["status"] != "PASS":
        sys.exit(1)


if __name__ == "__main__":
    main()
