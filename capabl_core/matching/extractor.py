"""
Deterministic Skill & Requirement Extraction Mechanism.

CAPABL Track 6 Requirement:
- Identifies technical skills from Resume and Job Description texts.
- Distinguishes required skills in JDs using explicit requirement keywords.
- Preserves exact source evidence (document source, page, line excerpt) for resumes.
- Avoids false matches (e.g., matching English substrings like 'go' in 'good' or 'c' in 'company').
- Extensible vocabulary of standard recruitment technologies.
"""

import re
from typing import List, Dict, Set, Optional, Union
from langchain_core.documents import Document

from capabl_core.matching.models import SkillEvidence
from capabl_core.matching.normalizer import normalize_skill


# Predefined technical vocabulary catalog
# Maps canonical skill names to recognized regex search patterns
TECHNICAL_SKILL_PATTERNS: Dict[str, str] = {
    # Programming Languages
    "python": r"(?<!\w)(?:python|py)(?!\w)",
    "javascript": r"(?<!\w)(?:javascript|js)(?!\w)",
    "typescript": r"(?<!\w)(?:typescript|ts)(?!\w)",
    "go": r"(?<!\w)(?:golang|go\b(?=[,\s/;\n]|$))",
    "rust": r"(?<!\w)rust(?!\w)",
    "java": r"(?<!\w)java(?!\w)(?!script)",
    "c++": r"(?<![\w+])(?:c\+\+|cpp)(?![\w+])",
    "c#": r"(?<![\w#])(?:c#|csharp)(?![\w#])",
    "c": r"(?<![\w#+])\bC\b(?![\w#+])",

    # Frameworks & Web
    "fastapi": r"(?<!\w)fastapi(?!\w)",
    "django": r"(?<!\w)django(?!\w)",
    "flask": r"(?<!\w)flask(?!\w)",
    "react": r"(?<!\w)(?:react|reactjs|react\.js)(?!\w)",
    "next.js": r"(?<!\w)(?:nextjs|next\.js)(?!\w)",
    "angular": r"(?<!\w)(?:angular|angularjs)(?!\w)",
    "vue": r"(?<!\w)(?:vue|vuejs|vue\.js)(?!\w)",
    "node.js": r"(?<!\w)(?:nodejs|node\.js|node)(?!\w)",
    "spring": r"(?<!\w)(?:spring|spring\s+boot)(?!\w)",
    ".net": r"(?<!\w)(?:\.net|dotnet)(?!\w)",

    # Databases & Caching
    "postgresql": r"(?<!\w)(?:postgresql|postgres|psql)(?!\w)",
    "mysql": r"(?<!\w)mysql(?!\w)",
    "mongodb": r"(?<!\w)(?:mongodb|mongo)(?!\w)",
    "redis": r"(?<!\w)redis(?!\w)",
    "sqlite": r"(?<!\w)sqlite(?!\w)",
    "cassandra": r"(?<!\w)cassandra(?!\w)",

    # Cloud & DevOps Infrastructure
    "aws": r"(?<!\w)(?:aws|amazon\s+web\s+services)(?!\w)",
    "azure": r"(?<!\w)(?:azure|microsoft\s+azure)(?!\w)",
    "gcp": r"(?<!\w)(?:gcp|google\s+cloud(?:\s+platform)?)(?!\w)",
    "docker": r"(?<!\w)docker(?!\w)",
    "kubernetes": r"(?<!\w)(?:kubernetes|k8s)(?!\w)",
    "terraform": r"(?<!\w)terraform(?!\w)",
    "helm": r"(?<!\w)helm(?!\w)",

    # Tools, Protocols & Architecture
    "git": r"(?<!\w)git(?!\w)(?!hub)",
    "github": r"(?<!\w)github(?!\w)",
    "linux": r"(?<!\w)linux(?!\w)",
    "rest": r"(?<!\w)(?:rest|restful)(?:\s+apis?)?(?!\w)",
    "graphql": r"(?<!\w)graphql(?!\w)",
    "kafka": r"(?<!\w)(?:apache\s+)?kafka(?!\w)",
    "rabbitmq": r"(?<!\w)rabbitmq(?!\w)",
    "tailwind css": r"(?<!\w)(?:tailwind(?:\s+css)?|tailwindcss)(?!\w)",
    "langchain": r"(?<!\w)langchain(?!\w)",
    "ci/cd": r"(?<![\w/])ci/cd(?![\w/])",
    "microservices": r"(?<!\w)microservices?(?!\w)",
    "jest": r"(?<!\w)jest(?!\w)",
    "html": r"(?<!\w)(?:html5?)(?!\w)",
    "css": r"(?<!\w)(?:css3?)(?!\w)",
}

# Compile patterns once for deterministic, high-performance extraction
COMPILED_SKILL_PATTERNS = {
    skill: re.compile(pattern, re.IGNORECASE)
    for skill, pattern in TECHNICAL_SKILL_PATTERNS.items()
}

# Requirement cues used to detect mandatory requirements in job descriptions
REQUIREMENT_CUES = [
    r"required\s+qualifications?",
    r"key\s+responsibilities",
    r"requirements?",
    r"must\s+have",
    r"mandatory",
    r"strong\s+experience\s+with",
    r"proficiency\s+in",
    r"experience\s+with",
    r"knowledge\s+of",
    r"qualifications?",
    r"what\s+you(?:'ll)?\s+need",
]
COMPILED_REQUIREMENT_CUE = re.compile(r"|".join(REQUIREMENT_CUES), re.IGNORECASE)


def extract_skills_from_text(text: str) -> List[str]:
    """
    Extracts canonical skill names present in the provided text.

    Args:
        text: Plain text content.

    Returns:
        List[str]: Sorted list of unique canonical skill names detected.
    """
    if not text:
        return []

    found_skills: Set[str] = set()
    for canonical_skill, pattern in COMPILED_SKILL_PATTERNS.items():
        if pattern.search(text):
            found_skills.add(normalize_skill(canonical_skill))

    return sorted(list(found_skills))


def extract_skills_with_evidence(
    documents_or_text: Union[str, List[Document]],
    default_source: str = "unknown",
    default_document_id: Optional[str] = None,
) -> Dict[str, List[SkillEvidence]]:
    """
    Extracts skills and attaches exact source evidence (document, page, excerpt).

    Args:
        documents_or_text: String text or list of LangChain Document objects with metadata.
        default_source: Fallback source name if string is provided.
        default_document_id: Fallback document ID if string is provided.

    Returns:
        Dict[str, List[SkillEvidence]]: Map of canonical skill name to list of SkillEvidence citations.
    """
    evidence_map: Dict[str, List[SkillEvidence]] = {}

    if isinstance(documents_or_text, str):
        docs = [
            Document(
                page_content=documents_or_text,
                metadata={"source": default_source, "page": 0, "document_id": default_document_id},
            )
        ]
    else:
        docs = documents_or_text

    for doc in docs:
        page_content = doc.page_content or ""
        meta = doc.metadata or {}
        source = meta.get("source", default_source)
        page = meta.get("page")
        doc_id = meta.get("document_id", default_document_id)

        # Split content into lines to isolate clean excerpts
        lines = [line.strip() for line in page_content.splitlines() if line.strip()]

        for canonical_skill, pattern in COMPILED_SKILL_PATTERNS.items():
            norm_skill = normalize_skill(canonical_skill)

            for line in lines:
                if pattern.search(line):
                    # Clean excerpt: trim long lines if necessary
                    excerpt = line if len(line) <= 250 else line[:247] + "..."
                    evidence_item = SkillEvidence(
                        skill=norm_skill,
                        source=str(source),
                        page=int(page) if page is not None else None,
                        document_id=str(doc_id) if doc_id else None,
                        excerpt=excerpt,
                    )

                    if norm_skill not in evidence_map:
                        evidence_map[norm_skill] = []

                    # Avoid duplicate excerpts for the same skill on the same page
                    is_duplicate = any(
                        e.excerpt == evidence_item.excerpt and e.page == evidence_item.page
                        for e in evidence_map[norm_skill]
                    )
                    if not is_duplicate:
                        evidence_map[norm_skill].append(evidence_item)

    return evidence_map


def extract_required_skills(
    documents_or_text: Union[str, List[Document]]
) -> List[str]:
    """
    Extracts required skills from Job Description text or documents.

    Distinguishes requirement sections (e.g. 'Required Qualifications', 'Key Responsibilities',
    'Must have') from purely optional/preferred skills where possible. If explicit requirement
    sections are absent, extracts all technical skills found in the JD.

    Args:
        documents_or_text: String text or list of LangChain Document objects representing JD.

    Returns:
        List[str]: Sorted list of unique canonical required skills.
    """
    if isinstance(documents_or_text, str):
        full_text = documents_or_text
    else:
        full_text = "\n".join(doc.page_content for doc in documents_or_text if doc.page_content)

    if not full_text.strip():
        return []

    lines = full_text.splitlines()
    required_text_blocks: List[str] = []
    in_required_block = False
    in_preferred_block = False

    for line in lines:
        clean_line = line.strip()
        if not clean_line:
            continue

        # Check for preferred / nice-to-have section boundaries
        if re.search(r"preferred\s+skills?|nice\s+to\s+have|bonus", clean_line, re.IGNORECASE):
            in_preferred_block = True
            in_required_block = False
            continue

        # Check for required section boundaries
        if COMPILED_REQUIREMENT_CUE.search(clean_line):
            in_required_block = True
            in_preferred_block = False
            required_text_blocks.append(clean_line)
            continue

        # If currently inside a required block, accumulate lines until a new header is hit
        if in_required_block and not in_preferred_block:
            required_text_blocks.append(clean_line)

    # If requirement blocks were identified, extract skills from those blocks
    if required_text_blocks:
        required_text = " \n ".join(required_text_blocks)
        extracted = extract_skills_from_text(required_text)
        if extracted:
            return extracted

    # Fallback baseline: extract all recognized technical skills from the JD text
    return extract_skills_from_text(full_text)
