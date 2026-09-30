"""
Evaluation Metrics for MCP External Tool Layer.

Milestone 9: External Tool Integration, MCP Boundary & Advanced Agent Capabilities.
Calculates strictly empirical metrics for:
- Tool discovery accuracy
- Tool argument validation rate
- Domain & candidate isolation pass rate
- Authorization gatekeeper adherence (booking confirmation)
- Prompt injection defense rate
- Overall MCP pass rate
"""

from typing import List, Dict, Any


def calculate_mcp_metrics(case_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Computes empirical evaluation metrics from individual case evaluation records.
    Never fabricates scores; purely derived from test case assertions.
    """
    total = len(case_results)
    if total == 0:
        return {
            "total_cases": 0,
            "overall_mcp_pass_rate": 0.0,
        }

    passed_count = sum(1 for c in case_results if c.get("passed", False))

    # Categorical counts
    discovery_cases = [c for c in case_results if c.get("category") == "tool_discovery"]
    isolation_cases = [c for c in case_results if "isolation" in c.get("category", "")]
    gate_cases = [c for c in case_results if c.get("category") == "authorization_gate"]
    injection_cases = [c for c in case_results if c.get("category") == "prompt_injection"]
    validation_cases = [c for c in case_results if c.get("category") == "security_validation"]
    execution_cases = [c for c in case_results if c.get("category") in ("tool_execution", "calendar_query")]

    def _rate(subset: List[Dict[str, Any]]) -> float:
        if not subset:
            return 1.0
        return round(sum(1 for c in subset if c.get("passed", False)) / len(subset), 4)

    return {
        "total_cases": total,
        "passed_cases": passed_count,
        "failed_cases": total - passed_count,
        "overall_mcp_pass_rate": round(passed_count / total, 4),
        "tool_discovery_accuracy": _rate(discovery_cases),
        "tool_execution_accuracy": _rate(execution_cases),
        "isolation_preservation_rate": _rate(isolation_cases),
        "authorization_gate_enforcement_rate": _rate(gate_cases),
        "prompt_injection_defense_rate": _rate(injection_cases),
        "security_validation_rate": _rate(validation_cases),
    }
