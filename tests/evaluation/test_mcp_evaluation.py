"""
Tests for MCP Evaluation Suite and Metrics.

Milestone 9: External Tool Integration, MCP Boundary & Advanced Agent Capabilities.
Verifies:
- MCP metric calculation logic
- MCP evaluation runner execution and benchmark generation
- Zero regressions in tool discovery, isolation, and gatekeeper enforcement
"""

import pytest
from evaluation.metrics.mcp_metrics import calculate_mcp_metrics
from evaluation.runners.mcp_runner import run_mcp_evaluation


class TestMCPEvaluationMetrics:

    def test_01_metrics_calculation(self):
        """Verify metric calculation over mock case results."""
        batch = [
            {"case_id": "c1", "category": "tool_discovery", "passed": True},
            {"case_id": "c2", "category": "candidate_isolation", "passed": True},
            {"case_id": "c3", "category": "authorization_gate", "passed": True},
            {"case_id": "c4", "category": "prompt_injection", "passed": True},
            {"case_id": "c5", "category": "security_validation", "passed": True},
        ]
        metrics = calculate_mcp_metrics(batch)
        assert metrics["total_cases"] == 5
        assert metrics["passed_cases"] == 5
        assert metrics["failed_cases"] == 0
        assert metrics["overall_mcp_pass_rate"] == 1.0
        assert metrics["tool_discovery_accuracy"] == 1.0
        assert metrics["isolation_preservation_rate"] == 1.0
        assert metrics["authorization_gate_enforcement_rate"] == 1.0
        assert metrics["prompt_injection_defense_rate"] == 1.0


class TestMCPEvaluationRunner:

    def test_02_run_mcp_evaluation_execution(self):
        """Verify empirical MCP evaluation runner passes all dataset cases."""
        result = run_mcp_evaluation()
        assert result["suite"] == "mcp"
        assert result["cases"] >= 10
        assert result["status"] == "PASS"
        assert result["failed"] == 0
        assert result["metrics"]["overall_mcp_pass_rate"] == 1.0
        assert result["metrics"]["isolation_preservation_rate"] == 1.0
        assert result["metrics"]["authorization_gate_enforcement_rate"] == 1.0
        assert result["metrics"]["prompt_injection_defense_rate"] == 1.0
