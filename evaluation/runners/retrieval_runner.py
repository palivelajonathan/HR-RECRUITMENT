"""
Retrieval Evaluation Runner.

CAPABL Track 6 Requirement:
- Evaluates retrieval precision, recall, MRR, and domain isolation against indexed Chroma vector store.
- Uses real synthetic documents: resume_alex_chen.pdf, resume_priya_sharma.pdf,
  jd_senior_backend_lead.pdf, policy_leave_and_attendance.pdf.
- Never fabricates results: records actual retrieval hits and ranks.
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from capabl_core.rag.vectorstore import ChromaVectorStoreManager
from capabl_core.rag.retriever import RecruitmentRetriever
from capabl_core.workflow.service import AutomaticMatchService
from evaluation.metrics.retrieval_metrics import (
    calculate_retrieval_metrics,
    normalize_source_name,
)


def ensure_test_documents_indexed(service: AutomaticMatchService) -> None:
    """Ensures the 4 standard synthetic PDFs are indexed into Chroma."""
    samples = [
        ("data/sample/resumes/resume_alex_chen.pdf", "resume", "alex_chen", "alex_chen", None),
        ("data/sample/resumes/resume_priya_sharma.pdf", "resume", "priya_sharma", "priya_sharma", None),
        ("data/sample/job_descriptions/jd_senior_backend_lead.pdf", "job_description", "jd_backend_lead_2026", None, "jd_backend_lead_2026"),
        ("data/sample/policies/policy_leave_and_attendance.pdf", "policy", "policy_leave_2026", None, None),
    ]
    for path_str, doc_type, doc_id, cand_id, j_id in samples:
        p = Path(path_str)
        if p.exists():
            service.ingest_document(
                file_path_or_bytes=str(p),
                document_type=doc_type,
                document_id=doc_id,
                candidate_id=cand_id,
                job_id=j_id,
                filename=p.name,
                replace=True,
            )


def run_retrieval_evaluation(
    dataset_path: Optional[Path] = None,
    vectorstore_manager: Optional[ChromaVectorStoreManager] = None,
) -> Dict[str, Any]:
    """
    Executes the retrieval evaluation suite and returns structured results.
    """
    mgr = vectorstore_manager or ChromaVectorStoreManager()
    service = AutomaticMatchService(vectorstore_manager=mgr)
    ensure_test_documents_indexed(service)

    retriever = RecruitmentRetriever(vectorstore_or_manager=mgr)

    data_file = dataset_path or Path("evaluation/datasets/retrieval_cases.json")
    if not data_file.exists():
        raise FileNotFoundError(f"Retrieval evaluation dataset not found at {data_file}")

    with open(data_file, "r", encoding="utf-8") as f:
        cases: List[Dict[str, Any]] = json.load(f)

    evaluation_records: List[Dict[str, Any]] = []
    case_results: List[Dict[str, Any]] = []
    passed_count = 0
    failed_count = 0

    for case in cases:
        cid = case["case_id"]
        query = case["query"]
        doc_type = case.get("document_type")
        expected_sources = [normalize_source_name(s) for s in case.get("expected_sources", [])]
        forbidden_sources = [normalize_source_name(s) for s in case.get("forbidden_sources", [])]

        candidate_id = case.get("candidate_id")
        job_id = case.get("job_id")
        policy_cat = case.get("policy_category")

        # Execute targeted retrieval based on domain type
        if doc_type == "resume" and candidate_id:
            docs = retriever.retrieve_candidate_evidence(candidate_id=candidate_id, query=query, top_k=5)
        elif doc_type == "job_description" and job_id:
            docs = retriever.retrieve_job_evidence(job_id=job_id, query=query, top_k=5)
        elif doc_type == "policy":
            docs = retriever.retrieve_policy_evidence(query=query, policy_category=policy_cat, top_k=5)
        else:
            docs = retriever.retrieve(query=query, document_type=doc_type, top_k=5)

        retrieved_source_names = [normalize_source_name(d.metadata.get("source", "")) for d in docs]

        # Verify whether at least one expected source is present in top 5 and no forbidden sources are leaked
        has_hit = any(s in expected_sources for s in retrieved_source_names)
        no_leak = not any(s in forbidden_sources for s in retrieved_source_names)

        is_passed = has_hit and no_leak
        if is_passed:
            passed_count += 1
        else:
            failed_count += 1

        eval_item = {
            "case_id": cid,
            "category": case.get("category"),
            "query": query,
            "retrieved_sources": retrieved_source_names,
            "expected_sources": expected_sources,
            "forbidden_sources": forbidden_sources,
            "passed": is_passed,
        }
        evaluation_records.append(eval_item)
        case_results.append(eval_item)

    metrics = calculate_retrieval_metrics(evaluation_records)

    return {
        "suite": "retrieval",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "cases": len(cases),
        "passed": passed_count,
        "failed": failed_count,
        "status": "PASS" if failed_count == 0 else "FAIL",
        "metrics": metrics,
        "details": case_results,
    }
