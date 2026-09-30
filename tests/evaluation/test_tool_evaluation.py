"""
Unit & Integration Tests for Tool Evaluation Suite.

Tests:
1. Tool selection accuracy (positive match and forbidden exclusion).
2. Argument schema correctness evaluation.
3. Execution status correctness.
4. Booking confirmation gate enforcement (confirmed=False -> confirmation_required).
5. Tool runner execution across all tool test cases.
"""

import pytest
from evaluation.metrics.tool_metrics import (
    measure_tool_selection_accuracy,
    measure_argument_correctness,
    measure_execution_correctness,
    measure_confirmation_enforcement,
    calculate_tool_metrics,
)
from evaluation.runners.tool_runner import run_tool_evaluation


class TestToolMetrics:

    def test_01_tool_selection_accuracy(self):
        assert measure_tool_selection_accuracy("retrieve_candidate_evidence", "retrieve_candidate_evidence") == 1.0
        assert measure_tool_selection_accuracy("retrieve_candidate_evidence", "retrieve_policy_evidence") == 0.0

        # Forbidden tool triggers 0.0
        assert measure_tool_selection_accuracy(
            "retrieve_candidate_evidence",
            "retrieve_policy_evidence",
            forbidden_tools=["retrieve_policy_evidence"],
        ) == 0.0

    def test_02_argument_correctness(self):
        expected = {"candidate_id": "alex_chen", "query": "Python"}
        actual = {"candidate_id": "alex_chen", "query": "Python", "top_k": 5}
        assert measure_argument_correctness(expected, actual) == 1.0

        mismatched = {"candidate_id": "priya_sharma", "query": "Python"}
        assert measure_argument_correctness(expected, mismatched) < 1.0

    def test_03_execution_correctness(self):
        assert measure_execution_correctness("success", "success") == 1.0
        assert measure_execution_correctness("confirmation_required", "confirmation_required") == 1.0
        assert measure_execution_correctness("error", "success") == 0.0

    def test_04_confirmation_enforcement_gate(self):
        # Unconfirmed booking MUST result in confirmation_required
        assert measure_confirmation_enforcement(confirmed_flag=False, actual_status="confirmation_required") is True
        assert measure_confirmation_enforcement(confirmed_flag=False, actual_status="booked") is False

        # Confirmed booking MUST result in booked
        assert measure_confirmation_enforcement(confirmed_flag=True, actual_status="booked") is True
        assert measure_confirmation_enforcement(confirmed_flag=True, actual_status="confirmation_required") is False

    def test_05_tool_metric_aggregator(self):
        batch = [
            {
                "expected_tool": "tool_a",
                "actual_tool": "tool_a",
                "expected_arguments": {"x": 1},
                "actual_arguments": {"x": 1},
                "expected_status": "success",
                "actual_status": "success",
            }
        ]
        metrics = calculate_tool_metrics(batch)
        assert metrics["total_cases"] == 1
        assert metrics["selection_accuracy"] == 1.0
        assert metrics["argument_accuracy"] == 1.0
        assert metrics["execution_accuracy"] == 1.0


class TestToolRunnerIntegration:

    def test_06_tool_runner_execution(self):
        result = run_tool_evaluation()
        assert result["suite"] == "tools"
        assert result["cases"] >= 8
        assert result["status"] == "PASS"
        assert result["failed"] == 0
        assert result["metrics"]["selection_accuracy"] == 1.0
        assert result["metrics"]["confirmation_enforcement_rate"] == 1.0
