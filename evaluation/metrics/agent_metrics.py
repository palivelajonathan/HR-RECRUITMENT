"""
Agent Trajectory & Task Completion Evaluation Metrics.

CAPABL Track 6 Requirement:
- Trajectory Correctness: Did the agent invoke the right sequence of tools?
- Task Completion Rate: Did the final synthesis contain all required factual components?
- Domain Separation: Did candidate queries remain isolated from policy queries?
- Unnecessary Tool Calls: Number of extraneous tool invocations outside the required workflow.
- Deterministic Match Context Grounding: Answering immediately from active match context without redundant tools.
"""

from typing import List, Dict, Any, Optional


def measure_trajectory_correctness(
    actual_tools: List[str],
    expected_trajectory: List[str],
    forbidden_tools: Optional[List[str]] = None,
) -> float:
    """
    Evaluates whether the tool call sequence matches the expected trajectory.
    If expected_trajectory is empty (e.g. answering from match context), actual_tools should be empty.
    """
    clean_actual = [t.strip().lower() for t in actual_tools if t]
    clean_expected = [t.strip().lower() for t in expected_trajectory if t]

    if forbidden_tools:
        clean_forbidden = [f.strip().lower() for f in forbidden_tools if f]
        for t in clean_actual:
            if t in clean_forbidden:
                return 0.0

    if not clean_expected:
        return 1.0 if len(clean_actual) == 0 else 0.5

    # Check if all expected tools were invoked
    hits = sum(1 for exp in clean_expected if exp in clean_actual)
    return round(hits / float(len(clean_expected)), 4)


def measure_task_completion(
    answer: str,
    required_elements: List[str],
) -> float:
    """
    Measures the ratio of required factual key points present in the answer.
    """
    if not required_elements:
        return 1.0 if (answer and answer.strip()) else 0.0

    if not answer or not answer.strip():
        return 0.0

    answer_lower = answer.lower()
    hits = sum(1 for elem in required_elements if elem.lower() in answer_lower)
    return round(hits / float(len(required_elements)), 4)


def measure_domain_separation(
    query_category: str,
    invoked_tools: List[str],
    sources: List[Dict[str, Any]],
) -> bool:
    """
    Verifies that the agent did not contaminate domains:
    - Policy query: No candidate tools, no resume sources.
    - Candidate query: No policy tools, no policy sources.
    """
    clean_tools = [t.lower() for t in invoked_tools]
    clean_cat = query_category.lower()

    if "policy" in clean_cat:
        if any("candidate" in t or "resume" in t for t in clean_tools):
            return False
        for s in sources:
            if s.get("document_type") == "resume":
                return False

    if "candidate" in clean_cat:
        if any("policy" in t for t in clean_tools):
            return False
        for s in sources:
            if s.get("document_type") == "policy":
                return False

    return True


def count_unnecessary_tools(
    actual_tools: List[str],
    expected_tools: List[str],
) -> int:
    """
    Counts tools called that were not in the expected set.
    """
    clean_actual = [t.lower() for t in actual_tools]
    clean_expected = set(t.lower() for t in expected_tools)
    return sum(1 for t in clean_actual if t not in clean_expected)


def calculate_agent_metrics(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Aggregates agent trajectory and task completion metrics across a batch of test cases.
    """
    if not results:
        return {
            "total_cases": 0,
            "trajectory_correctness": 0.0,
            "task_completion_rate": 0.0,
            "domain_separation_rate": 1.0,
            "avg_unnecessary_tools": 0.0,
        }

    traj_list = []
    comp_list = []
    dom_passes = 0
    unnec_list = []

    for item in results:
        actual_tools = item.get("actual_tools", [])
        expected_traj = item.get("expected_trajectory", [])
        forbidden = item.get("forbidden_tools")
        answer = item.get("answer", "")
        req_elements = item.get("required_answer_elements", [])
        cat = item.get("category", "")
        sources = item.get("sources", [])

        traj_list.append(measure_trajectory_correctness(actual_tools, expected_traj, forbidden))
        comp_list.append(measure_task_completion(answer, req_elements))

        if measure_domain_separation(cat, actual_tools, sources):
            dom_passes += 1

        unnec_list.append(count_unnecessary_tools(actual_tools, expected_traj))

    total = len(results)
    return {
        "total_cases": total,
        "trajectory_correctness": round(sum(traj_list) / float(total), 4),
        "task_completion_rate": round(sum(comp_list) / float(total), 4),
        "domain_separation_rate": round(dom_passes / float(total), 4),
        "avg_unnecessary_tools": round(sum(unnec_list) / float(total), 2),
    }
