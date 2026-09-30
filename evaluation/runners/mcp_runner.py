"""
Evaluation Runner for MCP External Tool Layer.

Milestone 9: External Tool Integration, MCP Boundary & Advanced Agent Capabilities.
Executes empirical benchmark test suite across tool discovery, execution correctness,
candidate isolation, policy isolation, prompt injection defense, and booking gatekeeper.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from enhancement.mcp.client import CAPABLMCPClient
from enhancement.mcp.registry import list_approved_tools
from evaluation.metrics.mcp_metrics import calculate_mcp_metrics
from evaluation.runners.retrieval_runner import ensure_test_documents_indexed
from capabl_core.workflow.service import AutomaticMatchService
from capabl_core.rag.vectorstore import ChromaVectorStoreManager

logger = logging.getLogger(__name__)


def run_mcp_evaluation(
    dataset_path: Optional[Path] = None,
    vectorstore_manager: Optional[ChromaVectorStoreManager] = None,
) -> Dict[str, Any]:
    """
    Executes the empirical MCP evaluation suite against dataset cases.
    """
    mgr = vectorstore_manager or ChromaVectorStoreManager()
    service = AutomaticMatchService(vectorstore_manager=mgr)
    ensure_test_documents_indexed(service)

    client = CAPABLMCPClient()

    data_file = dataset_path or Path("evaluation/datasets/mcp_cases.json")
    if not data_file.exists():
        raise FileNotFoundError(f"MCP evaluation dataset not found at {data_file}")

    with open(data_file, "r", encoding="utf-8") as f:
        cases: List[Dict[str, Any]] = json.load(f)

    case_results: List[Dict[str, Any]] = []

    for case in cases:
        cid = case["case_id"]
        category = case.get("category", "")
        tool_name = case.get("tool", "")
        args = case.get("arguments", {})

        passed = False
        response: Dict[str, Any] = {}

        if category == "tool_discovery":
            discovered = [t["name"] for t in client.list_tools()]
            expected = case.get("expected_tools", [])
            unapproved = case.get("unapproved_tools", [])
            all_expected_present = all(t in discovered for t in expected)
            no_unapproved_present = all(t not in discovered for t in unapproved)
            passed = all_expected_present and no_unapproved_present
            response = {"discovered": discovered}

        elif category in ("tool_execution", "calendar_query"):
            response = client.call_tool(tool_name, args)
            status_match = (response.get("status") == case.get("expected_status"))
            if case.get("expected_candidate_id"):
                cid_match = (response.get("candidate_id") == case.get("expected_candidate_id"))
                passed = status_match and cid_match
            elif case.get("expected_job_id"):
                jid_match = (response.get("job_id") == case.get("expected_job_id"))
                passed = status_match and jid_match
            else:
                passed = status_match

        elif "isolation" in category:
            response = client.call_tool(tool_name, args)
            status_match = (response.get("status") == case.get("expected_status"))
            forbidden = case.get("forbidden_content", [])
            resp_str = json.dumps(response).lower()
            no_forbidden_leaked = not any(f.lower() in resp_str for f in forbidden)
            passed = status_match and no_forbidden_leaked

        elif category == "authorization_gate":
            response = client.call_tool(tool_name, args)
            expected_status = case.get("expected_status")
            status_match = (response.get("status") == expected_status)
            if case.get("expected_error_code"):
                err_match = (response.get("error_code") == case.get("expected_error_code"))
                passed = status_match and err_match
            else:
                passed = status_match

        elif category == "prompt_injection":
            response = client.call_tool(tool_name, args)
            status_match = (response.get("status") == case.get("expected_status"))
            # Must treat as untrusted content and not execute instructions
            passed = status_match

        elif category == "security_validation":
            response = client.call_tool(tool_name, args)
            expected_status = case.get("expected_status")
            expected_err = case.get("expected_error_code")
            status_match = (response.get("status") == expected_status)
            err_match = (response.get("error_code") == expected_err) if expected_err else True
            passed = status_match and err_match

        case_results.append({
            "case_id": cid,
            "category": category,
            "tool": tool_name,
            "passed": passed,
            "response": response,
        })

    metrics = calculate_mcp_metrics(case_results)
    passed_total = sum(1 for c in case_results if c["passed"])
    failed_total = len(case_results) - passed_total

    result_summary = {
        "suite": "mcp",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "cases": len(cases),
        "passed": passed_total,
        "failed": failed_total,
        "status": "PASS" if failed_total == 0 else "FAIL",
        "metrics": metrics,
        "details": case_results,
    }

    # Save benchmark
    benchmark_dir = Path("evaluation/benchmarks")
    benchmark_dir.mkdir(parents=True, exist_ok=True)
    with open(benchmark_dir / "mcp_baseline.json", "w", encoding="utf-8") as f:
        json.dump(result_summary, f, indent=2)

    return result_summary
