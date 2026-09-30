"""
Unit & Integration Tests for Agent Evaluation Suite.

Tests:
1. Trajectory correctness metrics.
2. Task completion rate calculation.
3. Domain separation enforcement.
4. Unnecessary tool detection.
5. Deterministic match grounding evaluation.
"""

import pytest
from evaluation.metrics.agent_metrics import (
    measure_trajectory_correctness,
    measure_task_completion,
    measure_domain_separation,
    count_unnecessary_tools,
    calculate_agent_metrics,
)


class TestAgentMetrics:

    def test_01_trajectory_correctness(self):
        actual = ["retrieve_candidate_evidence"]
        expected = ["retrieve_candidate_evidence"]
        assert measure_trajectory_correctness(actual, expected) == 1.0

        # With forbidden tool
        assert measure_trajectory_correctness(
            ["retrieve_candidate_evidence", "retrieve_policy_evidence"],
            ["retrieve_candidate_evidence"],
            forbidden_tools=["retrieve_policy_evidence"],
        ) == 0.0

        # Empty expected trajectory (match context follow-up)
        assert measure_trajectory_correctness([], []) == 1.0

    def test_02_task_completion(self):
        answer = "Alex Chen has extensive Python, FastAPI, and PostgreSQL experience at CloudTech."
        required = ["Python", "FastAPI", "PostgreSQL", "CloudTech"]
        assert measure_task_completion(answer, required) == 1.0

        incomplete_answer = "Alex Chen has Python experience."
        assert measure_task_completion(incomplete_answer, required) == 0.25

    def test_03_domain_separation(self):
        # Policy query calling candidate tool is violated
        assert measure_domain_separation(
            query_category="policy_retrieval",
            invoked_tools=["retrieve_candidate_evidence"],
            sources=[],
        ) is False

        # Clean policy query
        assert measure_domain_separation(
            query_category="policy_retrieval",
            invoked_tools=["retrieve_policy_evidence"],
            sources=[{"document_type": "policy"}],
        ) is True

    def test_04_unnecessary_tools_count(self):
        actual = ["retrieve_candidate_evidence", "retrieve_policy_evidence", "search_interview_slots"]
        expected = ["retrieve_candidate_evidence"]
        assert count_unnecessary_tools(actual, expected) == 2

    def test_05_agent_metrics_aggregator(self):
        batch = [
            {
                "actual_tools": ["retrieve_candidate_evidence"],
                "expected_trajectory": ["retrieve_candidate_evidence"],
                "forbidden_tools": ["retrieve_policy_evidence"],
                "answer": "Alex Chen knows Python and FastAPI.",
                "required_answer_elements": ["Python", "FastAPI"],
                "category": "candidate_query",
                "sources": [{"document_type": "resume"}],
            }
        ]
        metrics = calculate_agent_metrics(batch)
        assert metrics["total_cases"] == 1
        assert metrics["trajectory_correctness"] == 1.0
        assert metrics["task_completion_rate"] == 1.0
        assert metrics["domain_separation_rate"] == 1.0
        assert metrics["avg_unnecessary_tools"] == 0.0
