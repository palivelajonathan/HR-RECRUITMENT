"""
LLM Provider types, configuration schemas, and domain exceptions.

Supports the Dual LLM Provider Strategy:
- Local Development / Testing: ChatOllama -> Ollama -> Qwen 3 8B (CAPABL Core Required)
- Public Deployment: ChatGroq -> Groq API -> Configured hosted model
"""

import os
from enum import Enum
from typing import Optional
from dataclasses import dataclass


class LLMProvider(str, Enum):
    """Supported LLM provider identifiers."""
    OLLAMA = "ollama"
    GROQ = "groq"


class LLMConfigError(ValueError):
    """Raised when LLM configuration is missing, invalid, or improperly formatted."""
    pass


class LLMConnectionError(ConnectionError):
    """Raised when the specified LLM service is unreachable or fails health checks."""
    pass


@dataclass
class LLMConfig:
    """Centralized LLM configuration dataclass."""
    provider: str = LLMProvider.OLLAMA.value
    ollama_model: str = "qwen3:8b"
    ollama_base_url: str = "http://localhost:11434"
    ollama_temperature: float = 0.1
    groq_api_key: Optional[str] = None
    groq_model: Optional[str] = None
    groq_temperature: float = 0.1

    @classmethod
    def from_env(cls) -> "LLMConfig":
        """Loads configuration from environment variables with settings fallback."""
        env_provider = os.getenv("LLM_PROVIDER")
        env_ollama_model = os.getenv("OLLAMA_MODEL")
        env_ollama_base_url = os.getenv("OLLAMA_BASE_URL")
        env_ollama_temp = os.getenv("OLLAMA_TEMPERATURE")
        env_groq_key = os.getenv("GROQ_API_KEY")
        env_groq_model = os.getenv("GROQ_MODEL")
        env_groq_temp = os.getenv("GROQ_TEMPERATURE")

        try:
            from capabl_core.config.settings import get_settings
            cfg = get_settings()
            def_provider = cfg.llm_provider
            def_ollama_model = cfg.ollama_model
            def_ollama_base_url = cfg.ollama_base_url
            def_ollama_temp = cfg.ollama_temperature
            def_groq_key = cfg.groq_api_key
            def_groq_model = cfg.groq_model
            def_groq_temp = cfg.groq_temperature
        except Exception:
            def_provider = "ollama"
            def_ollama_model = "qwen3:8b"
            def_ollama_base_url = "http://localhost:11434"
            def_ollama_temp = 0.1
            def_groq_key = None
            def_groq_model = None
            def_groq_temp = 0.1

        provider = env_provider if env_provider is not None else def_provider
        ollama_model = env_ollama_model if env_ollama_model is not None else def_ollama_model
        ollama_base_url = env_ollama_base_url if env_ollama_base_url is not None else def_ollama_base_url
        ollama_temp = float(env_ollama_temp) if env_ollama_temp is not None else def_ollama_temp
        groq_key = env_groq_key if env_groq_key is not None else def_groq_key
        groq_model = env_groq_model if env_groq_model is not None else def_groq_model
        groq_temp = float(env_groq_temp) if env_groq_temp is not None else def_groq_temp

        return cls(
            provider=provider,
            ollama_model=ollama_model,
            ollama_base_url=ollama_base_url,
            ollama_temperature=ollama_temp,
            groq_api_key=groq_key,
            groq_model=groq_model,
            groq_temperature=groq_temp,
        )
