"""
Retrieval Evaluation Metrics.

CAPABL Track 6 Requirement:
- Precision@K (K=1, 3, 5): Ratio of relevant retrieved documents in top K.
- Recall@K (K=1, 3, 5): Ratio of relevant documents retrieved relative to total relevant.
- Mean Reciprocal Rank (MRR): Reciprocal of the rank of the first relevant document.
- Isolation Compliance: Binary check verifying zero presence of forbidden domain/candidate sources.
- Factual and unmanufactured: All metrics calculated directly from actual retrieval lists.
"""

from typing import List, Dict, Any, Optional


def normalize_source_name(source: str) -> str:
    """Normalizes source path to filename for robust comparison."""
    if not source:
        return ""
    clean = source.strip().lower().replace("\\", "/")
    return clean.split("/")[-1]


def precision_at_k(retrieved_sources: List[str], expected_sources: List[str], k: int) -> float:
    """
    Computes Precision@K:
        (relevant items in top K) / K
    """
    if k <= 0:
        return 0.0

    norm_expected = {normalize_source_name(s) for s in expected_sources if s}
    if not norm_expected:
        return 0.0

    top_k_retrieved = [normalize_source_name(s) for s in retrieved_sources[:k]]
    hits = sum(1 for s in top_k_retrieved if s in norm_expected)
    return round(hits / float(k), 4)


def recall_at_k(retrieved_sources: List[str], expected_sources: List[str], k: int) -> float:
    """
    Computes Recall@K:
        (relevant items in top K) / (total relevant items)
    """
    norm_expected = {normalize_source_name(s) for s in expected_sources if s}
    if not norm_expected:
        return 1.0

    top_k_retrieved = [normalize_source_name(s) for s in retrieved_sources[:k]]
    unique_hits = len(set(top_k_retrieved) & norm_expected)
    return round(unique_hits / float(len(norm_expected)), 4)


def reciprocal_rank(retrieved_sources: List[str], expected_sources: List[str]) -> float:
    """
    Computes Reciprocal Rank (RR):
        1 / rank of first relevant item in retrieved list (1-indexed).
        Returns 0.0 if no relevant items are retrieved.
    """
    norm_expected = {normalize_source_name(s) for s in expected_sources if s}
    if not norm_expected:
        return 0.0

    for idx, s in enumerate(retrieved_sources, start=1):
        if normalize_source_name(s) in norm_expected:
            return round(1.0 / float(idx), 4)
    return 0.0


def mean_reciprocal_rank(rr_scores: List[float]) -> float:
    """Computes Mean Reciprocal Rank (MRR) across all queries."""
    if not rr_scores:
        return 0.0
    return round(sum(rr_scores) / float(len(rr_scores)), 4)


def isolation_compliance(retrieved_sources: List[str], forbidden_sources: List[str]) -> bool:
    """
    Returns True if ZERO forbidden sources are present in retrieved results.
    Guarantees cross-candidate and cross-domain data isolation.
    """
    norm_forbidden = {normalize_source_name(s) for s in forbidden_sources if s}
    if not norm_forbidden:
        return True

    norm_retrieved = {normalize_source_name(s) for s in retrieved_sources if s}
    leaked = norm_retrieved & norm_forbidden
    return len(leaked) == 0


def calculate_retrieval_metrics(
    results: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Aggregates retrieval performance across a batch of evaluated retrieval test cases.

    Each item in results is expected to have:
      - 'retrieved_sources': List[str]
      - 'expected_sources': List[str]
      - 'forbidden_sources': Optional[List[str]]
    """
    if not results:
        return {
            "total_cases": 0,
            "precision_at_1": 0.0,
            "precision_at_3": 0.0,
            "precision_at_5": 0.0,
            "recall_at_1": 0.0,
            "recall_at_3": 0.0,
            "recall_at_5": 0.0,
            "mrr": 0.0,
            "isolation_pass_rate": 1.0,
        }

    p1_list = []
    p3_list = []
    p5_list = []
    r1_list = []
    r3_list = []
    r5_list = []
    rr_list = []
    isolation_passes = 0

    for item in results:
        retrieved = item.get("retrieved_sources", [])
        expected = item.get("expected_sources", [])
        forbidden = item.get("forbidden_sources", [])

        p1_list.append(precision_at_k(retrieved, expected, k=1))
        p3_list.append(precision_at_k(retrieved, expected, k=3))
        p5_list.append(precision_at_k(retrieved, expected, k=5))

        r1_list.append(recall_at_k(retrieved, expected, k=1))
        r3_list.append(recall_at_k(retrieved, expected, k=3))
        r5_list.append(recall_at_k(retrieved, expected, k=5))

        rr_list.append(reciprocal_rank(retrieved, expected))

        if isolation_compliance(retrieved, forbidden):
            isolation_passes += 1

    total = len(results)
    return {
        "total_cases": total,
        "precision_at_1": round(sum(p1_list) / float(total), 4),
        "precision_at_3": round(sum(p3_list) / float(total), 4),
        "precision_at_5": round(sum(p5_list) / float(total), 4),
        "recall_at_1": round(sum(r1_list) / float(total), 4),
        "recall_at_3": round(sum(r3_list) / float(total), 4),
        "recall_at_5": round(sum(r5_list) / float(total), 4),
        "mrr": mean_reciprocal_rank(rr_list),
        "isolation_pass_rate": round(isolation_passes / float(total), 4),
    }
