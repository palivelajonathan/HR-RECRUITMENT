"""
Unit & Integration Tests for Retrieval Evaluation Suite.

Tests:
1. Precision@K calculation accuracy across edge cases.
2. Recall@K calculation accuracy.
3. Reciprocal Rank and Mean Reciprocal Rank (MRR).
4. Isolation compliance logic (detects leaked sources, passes clean).
5. Retrieval runner execution against indexed synthetic documents.
"""

import pytest
from evaluation.metrics.retrieval_metrics import (
    precision_at_k,
    recall_at_k,
    reciprocal_rank,
    mean_reciprocal_rank,
    isolation_compliance,
    calculate_retrieval_metrics,
)
from evaluation.runners.retrieval_runner import run_retrieval_evaluation


class TestRetrievalMetrics:

    def test_01_precision_at_k_exact_matches(self):
        retrieved = ["doc_a.pdf", "doc_b.pdf", "doc_c.pdf"]
        expected = ["doc_a.pdf"]
        assert precision_at_k(retrieved, expected, k=1) == 1.0
        assert precision_at_k(retrieved, expected, k=3) == round(1 / 3.0, 4)

    def test_02_precision_at_k_zero_hits_and_empty(self):
        assert precision_at_k(["doc_x.pdf"], ["doc_a.pdf"], k=1) == 0.0
        assert precision_at_k([], ["doc_a.pdf"], k=3) == 0.0
        assert precision_at_k(["doc_a.pdf"], [], k=3) == 0.0

    def test_03_recall_at_k(self):
        retrieved = ["doc_a.pdf", "doc_b.pdf"]
        expected = ["doc_a.pdf", "doc_b.pdf", "doc_c.pdf"]
        assert recall_at_k(retrieved, expected, k=2) == round(2 / 3.0, 4)
        assert recall_at_k(retrieved, expected, k=1) == round(1 / 3.0, 4)

    def test_04_reciprocal_rank_and_mrr(self):
        assert reciprocal_rank(["doc_a.pdf", "doc_b.pdf"], ["doc_a.pdf"]) == 1.0
        assert reciprocal_rank(["doc_x.pdf", "doc_a.pdf"], ["doc_a.pdf"]) == 0.5
        assert reciprocal_rank(["doc_x.pdf", "doc_y.pdf", "doc_a.pdf"], ["doc_a.pdf"]) == round(1 / 3.0, 4)
        assert reciprocal_rank(["doc_x.pdf", "doc_y.pdf"], ["doc_a.pdf"]) == 0.0

        rr_scores = [1.0, 0.5, 0.0]
        assert mean_reciprocal_rank(rr_scores) == 0.5

    def test_05_isolation_compliance(self):
        retrieved = ["resume_alex_chen.pdf", "other.pdf"]
        forbidden = ["resume_priya_sharma.pdf", "policy_leave.pdf"]
        assert isolation_compliance(retrieved, forbidden) is True

        leaked_retrieved = ["resume_alex_chen.pdf", "resume_priya_sharma.pdf"]
        assert isolation_compliance(leaked_retrieved, forbidden) is False

    def test_06_batch_metric_aggregator(self):
        batch = [
            {
                "retrieved_sources": ["a.pdf", "b.pdf"],
                "expected_sources": ["a.pdf"],
                "forbidden_sources": ["c.pdf"],
            },
            {
                "retrieved_sources": ["x.pdf", "y.pdf"],
                "expected_sources": ["y.pdf"],
                "forbidden_sources": ["z.pdf"],
            },
        ]
        metrics = calculate_retrieval_metrics(batch)
        assert metrics["total_cases"] == 2
        assert metrics["precision_at_1"] == 0.5  # Case 1 hit at 1, Case 2 hit at 2
        assert metrics["isolation_pass_rate"] == 1.0


class TestRetrievalRunnerIntegration:

    def test_07_run_retrieval_evaluation_suite(self):
        result = run_retrieval_evaluation()
        assert result["suite"] == "retrieval"
        assert result["cases"] >= 7
        assert result["status"] == "PASS"
        assert result["failed"] == 0
        assert result["metrics"]["isolation_pass_rate"] == 1.0
        assert result["metrics"]["mrr"] > 0.0
