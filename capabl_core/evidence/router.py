"""
Evidence Router for Milestone 6: Policy & Evidence Layer.

Provides query classification and routing guidance to ensure:
- Policy questions route to policy evidence.
- Candidate questions route to resume evidence.
- Job requirement questions route to job description evidence.
- Match/gap questions route to deterministic match context.
- Calendar questions route to interview calendar tools.
"""

import re
from enum import Enum
from typing import Optional


class QueryIntent(str, Enum):
    """Semantic intent classification of recruiter queries."""
    POLICY = "policy"
    CANDIDATE = "candidate"
    JOB_DESCRIPTION = "job_description"
    MATCH = "match"
    CALENDAR = "calendar"
    GENERAL = "general"


POLICY_KEYWORDS = [
    r"\bleave\b",
    r"\bpto\b",
    r"\bvacation\b",
    r"\bsick\b",
    r"\bsabbatical\b",
    r"\bpolicy\b",
    r"\bpolicies\b",
    r"\bhandbook\b",
    r"\bremote work\b",
    r"\bcore hours\b",
    r"\bwork from home\b",
    r"\bbenefit\b",
    r"\bbenefits\b",
    r"\bcompensation\b",
    r"\bhealth insurance\b",
    r"\battendance\b",
    r"\bmaternity\b",
    r"\bpaternity\b",
    r"\bnotice period\b",
    r"\bcompany rule\b",
    r"\bcompany rules\b",
    r"\bguidelines\b",
    r"\bcode of conduct\b",
]

MATCH_KEYWORDS = [
    r"\bmatch\b",
    r"\bmatching\b",
    r"\bfit\b",
    r"\bmissing skill\b",
    r"\bmissing skills\b",
    r"\bskills? are missing\b",
    r"\bmissing\b",
    r"\bskill gap\b",
    r"\bskill gaps\b",
    r"\bgap\b",
    r"\bgaps\b",
    r"\bsuitability\b",
    r"\balignment\b",
    r"\bevaluate candidate against\b",
    r"\bcompare resume\b",
    r"\bcompare candidate\b",
]

CALENDAR_KEYWORDS = [
    r"\binterview\b",
    r"\bslot\b",
    r"\bslots\b",
    r"\bschedule\b",
    r"\bscheduling\b",
    r"\bbook\b",
    r"\bbooking\b",
    r"\bavailable times\b",
    r"\bavailability\b",
    r"\bcalendar\b",
]

JOB_KEYWORDS = [
    r"\bjob description\b",
    r"\bjd\b",
    r"\brole require\b",
    r"\brole requires\b",
    r"\bposition require\b",
    r"\bposition requires\b",
    r"\brequirements for\b",
    r"\bmust have\b",
    r"\bqualifications for\b",
    r"\bresponsibilities for\b",
    r"\bjob requirements\b",
]

CANDIDATE_KEYWORDS = [
    r"\bresume\b",
    r"\bcandidate\b",
    r"\bexperience\b",
    r"\bbackground\b",
    r"\bworked at\b",
    r"\bworked with\b",
    r"\bprojects\b",
    r"\beducation\b",
    r"\bdegree\b",
    r"\balex\b",
    r"\bpriya\b",
]


def classify_query_intent(
    query: str,
    candidate_id: Optional[str] = None,
    job_id: Optional[str] = None,
) -> QueryIntent:
    """
    Deterministically classifies recruiter query into a discrete QueryIntent.
    Preserves separation between corporate policy, candidate background, and job specs.
    """
    clean_q = (query or "").lower().strip()

    # 1. Check for Calendar / Scheduling intent
    for pattern in CALENDAR_KEYWORDS:
        if re.search(pattern, clean_q):
            return QueryIntent.CALENDAR

    # 2. Check for Match / Gap analysis intent
    for pattern in MATCH_KEYWORDS:
        if re.search(pattern, clean_q):
            return QueryIntent.MATCH

    # 3. Check for Policy intent
    for pattern in POLICY_KEYWORDS:
        if re.search(pattern, clean_q):
            return QueryIntent.POLICY

    # 4. Check for Job Description intent
    for pattern in JOB_KEYWORDS:
        if re.search(pattern, clean_q):
            return QueryIntent.JOB_DESCRIPTION

    # 5. Check for Candidate intent
    for pattern in CANDIDATE_KEYWORDS:
        if re.search(pattern, clean_q):
            return QueryIntent.CANDIDATE

    if candidate_id and not job_id:
        return QueryIntent.CANDIDATE
    if job_id and not candidate_id:
        return QueryIntent.JOB_DESCRIPTION

    return QueryIntent.GENERAL
