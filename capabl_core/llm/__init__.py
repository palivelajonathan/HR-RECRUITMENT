"""
LLM Provider Abstraction Package.

Exposes a unified factory interface `create_llm()` supporting:
- Local Development / Testing: ChatOllama -> Ollama -> Qwen 3 8B (CAPABL Core Required)
- Public Deployment: ChatGroq -> Groq API -> Configured hosted model
"""

from capabl_core.llm.provider import (
    LLMProvider,
    LLMConfig,
    LLMConfigError,
    LLMConnectionError,
)
from capabl_core.llm.factory import create_llm, get_active_provider_name

__all__ = [
    "create_llm",
    "get_active_provider_name",
    "LLMProvider",
    "LLMConfig",
    "LLMConfigError",
    "LLMConnectionError",
]
