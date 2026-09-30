"""
Evaluation metrics for Retrieval, RAG, Tools, Agent, and Security.
"""

from evaluation.metrics.retrieval_metrics import (
    precision_at_k,
    recall_at_k,
    reciprocal_rank,
    mean_reciprocal_rank,
    isolation_compliance,
    calculate_retrieval_metrics,
)
from evaluation.metrics.rag_metrics import (
    measure_groundedness,
    measure_citation_accuracy,
    measure_unsupported_claim_rate,
    measure_relevance,
    calculate_rag_metrics,
)
from evaluation.metrics.tool_metrics import (
    measure_tool_selection_accuracy,
    measure_argument_correctness,
    measure_execution_correctness,
    measure_confirmation_enforcement,
    calculate_tool_metrics,
)
from evaluation.metrics.agent_metrics import (
    measure_trajectory_correctness,
    measure_task_completion,
    measure_domain_separation,
    count_unnecessary_tools,
    calculate_agent_metrics,
)
from evaluation.metrics.security_metrics import (
    measure_injection_resistance,
    measure_isolation_preservation,
    measure_booking_gate_security,
    measure_deterministic_immutability,
    calculate_security_metrics,
)

__all__ = [
    "precision_at_k",
    "recall_at_k",
    "reciprocal_rank",
    "mean_reciprocal_rank",
    "isolation_compliance",
    "calculate_retrieval_metrics",
    "measure_groundedness",
    "measure_citation_accuracy",
    "measure_unsupported_claim_rate",
    "measure_relevance",
    "calculate_rag_metrics",
    "measure_tool_selection_accuracy",
    "measure_argument_correctness",
    "measure_execution_correctness",
    "measure_confirmation_enforcement",
    "calculate_tool_metrics",
    "measure_trajectory_correctness",
    "measure_task_completion",
    "measure_domain_separation",
    "count_unnecessary_tools",
    "calculate_agent_metrics",
    "measure_injection_resistance",
    "measure_isolation_preservation",
    "measure_booking_gate_security",
    "measure_deterministic_immutability",
    "calculate_security_metrics",
]
