"""
Agent Trajectory & Task Completion Evaluation Runner.

CAPABL Track 6 Requirement:
- Evaluates full multi-step agent reasoning, tool trajectory selection, task completion,
  and grounding in active deterministic match context.
- Verifies that follow-up questions on missing skills are answered directly without altering skills.
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from capabl_core.rag.vectorstore import ChromaVectorStoreManager
from capabl_core.agent import create_recruitment_agent, run_recruitment_agent
from capabl_core.llm import create_llm
from capabl_core.matching import run_match
from capabl_core.workflow.service import AutomaticMatchService
from evaluation.runners.retrieval_runner import ensure_test_documents_indexed
from evaluation.metrics.agent_metrics import calculate_agent_metrics


def run_agent_evaluation(
    dataset_path: Optional[Path] = None,
    vectorstore_manager: Optional[ChromaVectorStoreManager] = None,
) -> Dict[str, Any]:
    """
    Executes the agent trajectory and task completion evaluation suite.
    """
    mgr = vectorstore_manager or ChromaVectorStoreManager()
    service = AutomaticMatchService(vectorstore_manager=mgr)
    ensure_test_documents_indexed(service)

    agent = create_recruitment_agent(llm=create_llm())

    data_file = dataset_path or Path("evaluation/datasets/agent_cases.json")
    if not data_file.exists():
        raise FileNotFoundError(f"Agent evaluation dataset not found at {data_file}")

    with open(data_file, "r", encoding="utf-8") as f:
        cases: List[Dict[str, Any]] = json.load(f)

    evaluation_records: List[Dict[str, Any]] = []
    case_results: List[Dict[str, Any]] = []
    passed_count = 0
    failed_count = 0

    for case in cases:
        cid = case["case_id"]
        query = case["query"]
        category = case.get("category", "")
        expected_traj = case.get("expected_trajectory", [])
        forbidden_tools = case.get("forbidden_tools", [])
        required_elements = case.get("required_answer_elements", [])
        use_match_context = case.get("use_active_match_context", False)

        active_match = None
        if use_match_context:
            cand_id = case.get("candidate_id") or "alex_chen"
            j_id = case.get("job_id") or "jd_backend_lead_2026"
            active_match = run_match(candidate_id=cand_id, job_id=j_id, vectorstore_manager=mgr)

        exec_result = run_recruitment_agent(
            agent=agent,
            query=query,
            match_context=active_match,
            session_id=f"eval_agent_{cid}",
        )

        invoked_tool_names = [tc.get("tool_name", "") for tc in exec_result.tool_calls]
        answer = exec_result.answer
        sources = exec_result.sources

        eval_record = {
            "case_id": cid,
            "category": category,
            "actual_tools": invoked_tool_names,
            "expected_trajectory": expected_traj,
            "forbidden_tools": forbidden_tools,
            "answer": answer,
            "required_answer_elements": required_elements,
            "sources": sources,
        }
        evaluation_records.append(eval_record)

        # Verification check
        # 1. No forbidden tools
        no_forbidden = not any(ft.lower() in [t.lower() for t in invoked_tool_names] for ft in forbidden_tools)
        # 2. Key elements present in answer
        elements_hit = sum(1 for el in required_elements if el.lower() in answer.lower())
        elements_ok = (elements_hit / float(len(required_elements))) >= 0.5 if required_elements else True

        case_passed = no_forbidden and elements_ok and (exec_result.status != "error")
        if case_passed:
            passed_count += 1
        else:
            failed_count += 1

        case_results.append({
            "case_id": cid,
            "passed": case_passed,
            "tools_invoked": invoked_tool_names,
            "answer_preview": answer[:150],
            "status": exec_result.status,
        })

    metrics = calculate_agent_metrics(evaluation_records)

    return {
        "suite": "agent",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "cases": len(cases),
        "passed": passed_count,
        "failed": failed_count,
        "status": "PASS" if failed_count == 0 else "FAIL",
        "metrics": metrics,
        "details": case_results,
    }
