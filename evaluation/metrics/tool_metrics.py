"""
Tool Calling Evaluation Metrics.

CAPABL Track 6 Requirement:
- Tool Selection Accuracy: Did the agent select the exact required tool?
- Argument Correctness: Did the arguments match the expected schema and entity values?
- Execution Correctness: Did the tool execute and return the expected status?
- Confirmation Enforcement: Did unconfirmed state mutations remain strictly blocked?
- Domain Tool Separation: Did the agent avoid calling forbidden cross-domain tools?
"""

from typing import List, Dict, Any, Optional


def measure_tool_selection_accuracy(
    expected_tool: str,
    actual_tool: Optional[str],
    forbidden_tools: Optional[List[str]] = None,
) -> float:
    """
    Evaluates whether the agent selected the correct tool and avoided forbidden tools.
    """
    if not actual_tool:
        return 0.0

    clean_actual = actual_tool.strip().lower()
    clean_expected = expected_tool.strip().lower()

    if forbidden_tools:
        clean_forbidden = [f.strip().lower() for f in forbidden_tools if f]
        if clean_actual in clean_forbidden:
            return 0.0

    return 1.0 if clean_actual == clean_expected else 0.0


def measure_argument_correctness(
    expected_args: Dict[str, Any],
    actual_args: Dict[str, Any],
) -> float:
    """
    Evaluates the accuracy of tool arguments against expected criteria.
    """
    if not expected_args:
        return 1.0

    if not actual_args:
        return 0.0

    matched_keys = 0
    for key, expected_val in expected_args.items():
        if key in actual_args:
            actual_val = actual_args[key]
            if isinstance(expected_val, str) and isinstance(actual_val, str):
                if expected_val.strip().lower() in actual_val.strip().lower():
                    matched_keys += 1
            elif expected_val == actual_val:
                matched_keys += 1

    return round(matched_keys / float(len(expected_args)), 4)


def measure_execution_correctness(
    actual_status: str,
    expected_status: str,
) -> float:
    """
    Evaluates whether tool execution returned the expected status code.
    """
    clean_actual = actual_status.strip().lower()
    clean_expected = expected_status.strip().lower()
    if clean_actual == clean_expected:
        return 1.0
    if clean_actual in ("success", "complete", "booked") and clean_expected in ("success", "complete", "booked"):
        return 1.0
    return 0.0


def measure_confirmation_enforcement(
    confirmed_flag: bool,
    actual_status: str,
) -> bool:
    """
    Enforces the booking confirmation gate rule:
    - If confirmed_flag is False, actual_status MUST be 'confirmation_required'.
    - If confirmed_flag is True, actual_status must be 'booked' or 'success'.
    """
    clean_status = actual_status.strip().lower()
    if not confirmed_flag:
        return clean_status == "confirmation_required"
    else:
        return clean_status in ("booked", "success")


def calculate_tool_metrics(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Aggregates tool metrics across a batch of evaluated tool scenarios.
    """
    if not results:
        return {
            "total_cases": 0,
            "selection_accuracy": 0.0,
            "argument_accuracy": 0.0,
            "execution_accuracy": 0.0,
            "confirmation_enforcement_rate": 1.0,
        }

    sel_list = []
    arg_list = []
    exec_list = []
    conf_checks = 0
    conf_passes = 0

    for item in results:
        expected_tool = item.get("expected_tool", "")
        actual_tool = item.get("actual_tool")
        forbidden = item.get("forbidden_tools")
        sel_list.append(measure_tool_selection_accuracy(expected_tool, actual_tool, forbidden))

        expected_args = item.get("expected_arguments", {})
        actual_args = item.get("actual_arguments", {})
        arg_list.append(measure_argument_correctness(expected_args, actual_args))

        expected_status = item.get("expected_status", "success")
        actual_status = item.get("actual_status", "success")
        exec_list.append(measure_execution_correctness(actual_status, expected_status))

        if "confirmed" in expected_args:
            conf_checks += 1
            is_confirmed = bool(expected_args["confirmed"])
            if measure_confirmation_enforcement(is_confirmed, actual_status):
                conf_passes += 1

    total = len(results)
    conf_rate = round(conf_passes / float(conf_checks), 4) if conf_checks > 0 else 1.0

    return {
        "total_cases": total,
        "selection_accuracy": round(sum(sel_list) / float(total), 4),
        "argument_accuracy": round(sum(arg_list) / float(total), 4),
        "execution_accuracy": round(sum(exec_list) / float(total), 4),
        "confirmation_enforcement_rate": conf_rate,
    }
