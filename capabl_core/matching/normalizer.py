"""
Deterministic Skill Normalization Layer.

CAPABL Track 6 Requirement:
- Normalizes skill identifiers to prevent syntactic mismatch (e.g. 'Postgres' vs 'PostgreSQL',
  'JS' vs 'JavaScript', 'Python' vs 'python').
- Controlled, explicit, and extensible alias dictionary.
- Deterministic string transformation with zero non-deterministic inference.
"""

import re
from typing import Dict

# Explicit, documented alias dictionary mapping synonyms to canonical terms
SKILL_ALIASES: Dict[str, str] = {
    # Programming Languages
    "py": "python",
    "python": "python",
    "js": "javascript",
    "javascript": "javascript",
    "ts": "typescript",
    "typescript": "typescript",
    "golang": "go",
    "go": "go",
    "c#": "c#",
    "csharp": "c#",
    "c++": "c++",
    "cpp": "c++",
    "rust": "rust",
    "java": "java",
    "c": "c",

    # Frameworks & Libraries
    "fastapi": "fastapi",
    "django": "django",
    "flask": "flask",
    "react": "react",
    "reactjs": "react",
    "react.js": "react",
    "nextjs": "next.js",
    "next.js": "next.js",
    "angular": "angular",
    "angularjs": "angular",
    "vue": "vue",
    "vuejs": "vue",
    "vue.js": "vue",
    "nodejs": "node.js",
    "node.js": "node.js",
    "node": "node.js",
    "spring": "spring",
    "spring boot": "spring",
    ".net": ".net",
    "dotnet": ".net",
    "dot net": ".net",

    # Databases & Storage
    "postgres": "postgresql",
    "postgresql": "postgresql",
    "psql": "postgresql",
    "mysql": "mysql",
    "mongo": "mongodb",
    "mongodb": "mongodb",
    "redis": "redis",
    "sqlite": "sqlite",
    "cassandra": "cassandra",

    # Cloud & Container Infrastructure
    "aws": "aws",
    "amazon web services": "aws",
    "azure": "azure",
    "microsoft azure": "azure",
    "gcp": "gcp",
    "google cloud": "gcp",
    "google cloud platform": "gcp",
    "docker": "docker",
    "k8s": "kubernetes",
    "kubernetes": "kubernetes",
    "terraform": "terraform",
    "helm": "helm",

    # Tools, Protocols & Architecture
    "git": "git",
    "github": "github",
    "linux": "linux",
    "rest": "rest",
    "rest api": "rest",
    "rest apis": "rest",
    "restful": "rest",
    "restful api": "rest",
    "graphql": "graphql",
    "kafka": "kafka",
    "apache kafka": "kafka",
    "rabbitmq": "rabbitmq",
    "tailwind": "tailwind css",
    "tailwind css": "tailwind css",
    "tailwindcss": "tailwind css",
    "langchain": "langchain",
    "ci/cd": "ci/cd",
    "cicd": "ci/cd",
    "microservices": "microservices",
    "jest": "jest",
    "html": "html",
    "html5": "html",
    "css": "css",
    "css3": "css",
}


def normalize_skill(skill: str) -> str:
    """
    Deterministically normalizes a raw skill string to its canonical representation.

    Steps:
    1. Lowercase and strip whitespace.
    2. Strip extraneous enclosing punctuation while preserving internal special tokens
       (e.g., '.net', 'c++', 'c#', 'node.js', 'ci/cd').
    3. Look up canonical alias in SKILL_ALIASES.
    4. If not found in alias map, return cleaned lowercase string.

    Args:
        skill: Raw skill name (e.g., 'PostgreSQL', 'JS', '  Python!  ').

    Returns:
        str: Canonical normalized skill identifier.
    """
    if not skill or not isinstance(skill, str):
        return ""

    raw = skill.strip().lower()

    # Strip surrounding quotes, brackets, and periods, but preserve leading dot for '.net'
    # and trailing pluses/hashes for 'c++', 'c#'
    cleaned = raw.strip(' "\'()[]{}<>,;:')

    # Check alias map directly
    if cleaned in SKILL_ALIASES:
        return SKILL_ALIASES[cleaned]

    # Additional cleanup: collapse multiple whitespace
    cleaned = re.sub(r"\s+", " ", cleaned)

    return SKILL_ALIASES.get(cleaned, cleaned)
