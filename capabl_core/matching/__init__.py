"""
Deterministic Resume ↔ Job Description Match Subsystem.

CAPABL Track 6 (HR / Recruitment).
"""

from capabl_core.matching.models import SkillEvidence, MatchResult
from capabl_core.matching.normalizer import normalize_skill, SKILL_ALIASES
from capabl_core.matching.extractor import (
    TECHNICAL_SKILL_PATTERNS,
    extract_skills_from_text,
    extract_skills_with_evidence,
    extract_required_skills,
)
from capabl_core.matching.matcher import compute_deterministic_match, run_match

__all__ = [
    "SkillEvidence",
    "MatchResult",
    "normalize_skill",
    "SKILL_ALIASES",
    "TECHNICAL_SKILL_PATTERNS",
    "extract_skills_from_text",
    "extract_skills_with_evidence",
    "extract_required_skills",
    "compute_deterministic_match",
    "run_match",
]
