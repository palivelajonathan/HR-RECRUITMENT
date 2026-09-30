"""
Unit & Integration Tests for RAG / Evidence Evaluation Suite.

Tests:
1. Groundedness measurement against factual contexts.
2. Citation accuracy calculation with and without structured citations.
3. Unsupported claim rate detection.
4. Relevance scoring for query-answer pairs.
5. RAG evaluation runner execution.
"""

import pytest
from evaluation.metrics.rag_metrics import (
    measure_groundedness,
    measure_citation_accuracy,
    measure_unsupported_claim_rate,
    measure_relevance,
    calculate_rag_metrics,
)
from evaluation.runners.rag_runner import run_rag_evaluation


class TestRAGMetrics:

    def test_01_groundedness_supported_claims(self):
        context = ["Alex Chen has 6.5 years of experience in distributed systems and Python."]
        answer = "Alex Chen has 6.5 years of experience working with Python."
        expected_claims = ["6.5 years", "Python"]
        score = measure_groundedness(answer, context, expected_claims)
        assert score == 1.0

    def test_02_groundedness_unsupported_claims(self):
        context = ["Alex Chen has 6.5 years of experience."]
        answer = "Alex Chen has 15 years of experience and is VP of Engineering."
        expected_claims = ["15 years", "VP of Engineering"]
        score = measure_groundedness(answer, context, expected_claims)
        assert score == 0.0

    def test_03_citation_accuracy(self):
        sources = [{"source": "resume_alex_chen.pdf", "page": 1, "document_id": "alex_chen"}]
        answer = "According to resume_alex_chen.pdf on page 1, the candidate knows Python."
        score = measure_citation_accuracy(answer, sources, requires_citation=True)
        assert score == 1.0

        empty_sources = []
        score_empty = measure_citation_accuracy(answer, empty_sources, requires_citation=True)
        assert score_empty == 0.0

    def test_04_unsupported_claim_rate(self):
        context = ["The company grants 24 days of annual leave."]
        answer = "The company grants 24 days of annual leave and unlimited sick days."
        forbidden = ["unlimited sick days"]
        rate = measure_unsupported_claim_rate(answer, context, forbidden_claims=forbidden)
        assert rate > 0.0

        clean_answer = "The company grants 24 days of annual leave."
        rate_clean = measure_unsupported_claim_rate(clean_answer, context, forbidden_claims=forbidden)
        assert rate_clean == 0.0

    def test_05_relevance_metric(self):
        query = "What backend languages does the candidate know?"
        answer = "The candidate knows Python, FastAPI, and PostgreSQL."
        assert measure_relevance(answer, query) > 0.0

    def test_06_rag_metric_aggregator(self):
        batch = [
            {
                "answer": "Alex knows Python.",
                "context_chunks": ["Alex has Python experience."],
                "sources": [{"source": "resume.pdf"}],
                "expected_claims": ["Python"],
                "requires_citation": True,
            }
        ]
        metrics = calculate_rag_metrics(batch)
        assert metrics["total_cases"] == 1
        assert metrics["groundedness"] == 1.0
        assert metrics["citation_accuracy"] > 0.0


class TestRAGRunnerIntegration:

    def test_07_rag_runner_execution_deterministic(self):
        # Run in deterministic mode (use_agent=False) to test pipeline and metrics
        result = run_rag_evaluation(use_agent=False)
        assert result["suite"] == "rag"
        assert result["cases"] >= 5
        assert result["status"] == "PASS"
        assert result["failed"] == 0
        assert result["metrics"]["groundedness"] > 0.0
