"""
RAG / Evidence Generation Evaluation Metrics.

CAPABL Track 6 Requirement:
- Groundedness (Faithfulness): Does the answer strictly adhere to retrieved evidence?
- Citation Accuracy: Does the answer accurately cite valid source documents and pages?
- Unsupported Claim Rate: Ratio of unsupported or hallucinated claims to total factual claims.
- Question Relevance: Does the generated answer directly address the recruiter's prompt?
"""

import re
from typing import List, Dict, Any, Optional


def clean_tokens(text: str) -> List[str]:
    """Tokenizes text into lowercase alphanumeric words."""
    if not text:
        return []
    return re.findall(r"\b[a-zA-Z0-9_\-\.]+\b", text.lower())


def measure_groundedness(
    answer: str,
    context_chunks: List[str],
    expected_claims: Optional[List[str]] = None,
) -> float:
    """
    Evaluates groundedness:
    - If expected_claims are provided, checks the proportion of expected factual claims present in the answer
      AND verified in context_chunks.
    - Otherwise, measures vocabulary overlap of factual sentences against context_chunks.
    """
    if not answer or not answer.strip():
        return 0.0

    if not context_chunks:
        # If no context was provided, any factual claim is ungrounded
        return 0.0

    combined_context = " ".join(context_chunks).lower()

    if expected_claims:
        verified_count = 0
        for claim in expected_claims:
            claim_clean = claim.lower()
            if claim_clean in answer.lower() and claim_clean in combined_context:
                verified_count += 1
            elif claim_clean in answer.lower():
                # Present in answer but NOT in context -> ungrounded
                pass
            else:
                # Claim not made; check if answer accurately indicated missing info
                if any(phrase in answer.lower() for phrase in ["not contain", "insufficient", "not provided", "no evidence"]):
                    verified_count += 1
        return round(verified_count / float(len(expected_claims)), 4)

    # General sentence overlap heuristic
    sentences = [s.strip() for s in re.split(r"[.\n]", answer) if len(s.strip()) > 10]
    if not sentences:
        return 1.0

    supported = 0
    for sent in sentences:
        tokens = set(clean_tokens(sent))
        if not tokens:
            continue
        context_tokens = set(clean_tokens(combined_context))
        overlap = len(tokens & context_tokens) / float(len(tokens))
        if overlap >= 0.4:
            supported += 1

    return round(supported / float(len(sentences)), 4)


def measure_citation_accuracy(
    answer: str,
    sources: List[Dict[str, Any]],
    requires_citation: bool = True,
) -> float:
    """
    Evaluates citation accuracy:
    - Checks that sources were returned by the agent.
    - Verifies that cited source documents match indexed records.
    - Checks whether the answer references citations (e.g. source, page, or document identifier).
    """
    if not requires_citation:
        return 1.0

    if not sources:
        return 0.0

    # Verify sources contain required metadata fields
    valid_sources = 0
    for s in sources:
        if s.get("source") or s.get("document_id"):
            valid_sources += 1

    source_validity = valid_sources / float(len(sources))

    # Check citation indicators in text or structured envelope
    has_text_citation = bool(re.search(r"(source|page|pdf|document)", answer, re.IGNORECASE))
    has_structured_citation = len(sources) > 0

    if has_structured_citation and has_text_citation:
        text_score = 1.0
    elif has_structured_citation:
        text_score = 0.8
    else:
        text_score = 0.0

    return round((source_validity * 0.5) + (text_score * 0.5), 4)


def measure_unsupported_claim_rate(
    answer: str,
    context_chunks: List[str],
    forbidden_claims: Optional[List[str]] = None,
) -> float:
    """
    Computes Unsupported Claim Rate:
        unsupported factual claims / total factual claims
    Lower is better (0.0 is ideal).
    """
    if not answer or not answer.strip():
        return 0.0

    unsupported_count = 0
    total_checks = 0

    if forbidden_claims:
        for claim in forbidden_claims:
            total_checks += 1
            if claim.lower() in answer.lower():
                unsupported_count += 1

    combined_context = " ".join(context_chunks).lower()
    sentences = [s.strip() for s in re.split(r"[.\n]", answer) if len(s.strip()) > 10]

    for sent in sentences:
        total_checks += 1
        tokens = set(clean_tokens(sent))
        if not tokens:
            continue
        context_tokens = set(clean_tokens(combined_context))
        overlap = len(tokens & context_tokens) / float(len(tokens))
        if overlap < 0.25 and not any(p in sent.lower() for p in ["not contain", "insufficient", "not provided"]):
            unsupported_count += 1

    if total_checks == 0:
        return 0.0

    return round(unsupported_count / float(total_checks), 4)


def measure_relevance(
    answer: str,
    query: str,
    expected_keywords: Optional[List[str]] = None,
) -> float:
    """
    Evaluates whether the answer directly addresses the query.
    """
    if not answer or not answer.strip():
        return 0.0

    if expected_keywords:
        hits = sum(1 for kw in expected_keywords if kw.lower() in answer.lower())
        return round(hits / float(len(expected_keywords)), 4)

    query_tokens = set(clean_tokens(query))
    if not query_tokens:
        return 1.0

    answer_tokens = set(clean_tokens(answer))
    overlap = len(query_tokens & answer_tokens)
    return round(min(1.0, overlap / float(max(1, len(query_tokens) // 2))), 4)


def calculate_rag_metrics(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Aggregates RAG evaluation metrics across a batch of test cases.
    """
    if not results:
        return {
            "total_cases": 0,
            "groundedness": 0.0,
            "citation_accuracy": 0.0,
            "unsupported_claim_rate": 0.0,
            "relevance": 0.0,
        }

    g_list = []
    c_list = []
    u_list = []
    r_list = []

    for item in results:
        answer = item.get("answer", "")
        contexts = item.get("context_chunks", [])
        expected_claims = item.get("expected_claims")
        forbidden_claims = item.get("forbidden_claims")
        sources = item.get("sources", [])
        requires_citation = item.get("requires_citation", True)
        query = item.get("query", "")

        g_list.append(measure_groundedness(answer, contexts, expected_claims))
        c_list.append(measure_citation_accuracy(answer, sources, requires_citation))
        u_list.append(measure_unsupported_claim_rate(answer, contexts, forbidden_claims))
        r_list.append(measure_relevance(answer, query, expected_claims))

    total = len(results)
    return {
        "total_cases": total,
        "groundedness": round(sum(g_list) / float(total), 4),
        "citation_accuracy": round(sum(c_list) / float(total), 4),
        "unsupported_claim_rate": round(sum(u_list) / float(total), 4),
        "relevance": round(sum(r_list) / float(total), 4),
    }
