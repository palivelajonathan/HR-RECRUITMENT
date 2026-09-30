"""
LLM Provider Factory.

Implements the single application-facing factory interface: `create_llm()`.
Decouples all downstream components (Agent, RAG, Tools, Memory, Orchestration, UI)
from concrete LLM provider implementations.

Dual Provider Routing:
- LLM_PROVIDER="ollama" -> ChatOllama (Ollama runtime, default: Qwen 3 8B) [CAPABL Required]
- LLM_PROVIDER="groq"   -> ChatGroq (Groq Cloud API, configured hosted model) [Public Deployment]
"""

import os
from typing import Optional, Any
from langchain_core.language_models.chat_models import BaseChatModel

from capabl_core.llm.provider import (
    LLMProvider,
    LLMConfig,
    LLMConfigError,
    LLMConnectionError,
)


def get_active_provider_name(config: Optional[LLMConfig] = None) -> str:
    """
    Returns the normalized name of the currently active LLM provider.

    Resolves active provider from the supplied LLMConfig or environment variable
    LLM_PROVIDER (defaulting to 'ollama'). Validates that the provider is supported,
    strictly prohibiting silent fallbacks to unconfigured or arbitrary backends.

    Args:
        config: Optional pre-loaded LLMConfig instance.

    Returns:
        str: 'ollama' or 'groq'.

    Raises:
        LLMConfigError: If configured provider is not in the supported LLMProvider enum.
    """
    active_config = config or LLMConfig.from_env()
    raw_provider = (active_config.provider or "").strip().lower()
    valid_providers = {p.value for p in LLMProvider}

    if raw_provider not in valid_providers:
        raise LLMConfigError(
            f"Unsupported LLM_PROVIDER: '{raw_provider}'. "
            f"Supported providers are: {sorted(valid_providers)}. "
            f"Silent fallback is prohibited; please configure a valid provider."
        )

    return raw_provider


def create_llm(
    provider: Optional[str] = None,
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    base_url: Optional[str] = None,
    api_key: Optional[str] = None,
    config: Optional[LLMConfig] = None,
    **kwargs: Any,
) -> BaseChatModel:
    """
    Constructs and returns an official LangChain BaseChatModel instance
    according to active configuration or explicit arguments.

    Args:
        provider: 'ollama' or 'groq'. Defaults to environment LLM_PROVIDER or 'ollama'.
        model: Specific model name override.
        temperature: Sampling temperature override (default: 0.1).
        base_url: Base URL override for Ollama daemon.
        api_key: API key override for Groq.
        config: Optional pre-loaded LLMConfig instance.
        **kwargs: Additional provider-specific keyword arguments passed to the constructor.

    Returns:
        BaseChatModel: An instantiated ChatOllama or ChatGroq model conforming
                       to LangChain's standard chat model interface.

    Raises:
        LLMConfigError: If provider is unsupported, or required credentials/model names are missing.
        LLMConnectionError: If connection to the provider fails during verification.
    """
    active_config = config or LLMConfig.from_env()

    resolved_provider = (
        provider or active_config.provider or LLMProvider.OLLAMA.value
    ).strip().lower()

    # --------------------------------------------------------------------------
    # 1. Ollama Provider Branch (CAPABL Core Required)
    # --------------------------------------------------------------------------
    if resolved_provider == LLMProvider.OLLAMA.value:
        resolved_model = model or active_config.ollama_model or "qwen3:8b"
        resolved_base_url = (
            base_url or active_config.ollama_base_url or "http://localhost:11434"
        )
        resolved_temp = (
            temperature
            if temperature is not None
            else active_config.ollama_temperature
        )

        try:
            from langchain_ollama import ChatOllama
        except ImportError as exc:
            raise LLMConfigError(
                "Package 'langchain-ollama' is required for the Ollama provider. "
                "Install it using: pip install langchain-ollama"
            ) from exc

        return ChatOllama(
            model=resolved_model,
            base_url=resolved_base_url,
            temperature=resolved_temp,
            **kwargs,
        )

    # --------------------------------------------------------------------------
    # 2. Groq Provider Branch (Public Deployment)
    # --------------------------------------------------------------------------
    elif resolved_provider == LLMProvider.GROQ.value:
        resolved_key = (api_key or active_config.groq_api_key or "").strip()
        if not resolved_key:
            raise LLMConfigError(
                "GROQ_API_KEY is missing or empty. When LLM_PROVIDER='groq', "
                "a valid GROQ_API_KEY must be provided via environment variable, "
                ".env file, or factory argument. Silent fallback to Ollama is strictly disallowed."
            )

        resolved_model = (model or active_config.groq_model or "").strip()
        if not resolved_model:
            raise LLMConfigError(
                "GROQ_MODEL is missing or empty. When LLM_PROVIDER='groq', "
                "a valid hosted model name must be configured (e.g., 'llama-3.3-70b-versatile', "
                "'mixtral-8x7b-32768'). Hard-coding a default Groq model is disallowed."
            )

        resolved_temp = (
            temperature
            if temperature is not None
            else active_config.groq_temperature
        )

        try:
            from langchain_groq import ChatGroq
        except ImportError as exc:
            raise LLMConfigError(
                "Package 'langchain-groq' is required for the Groq provider. "
                "Install it using: pip install langchain-groq"
            ) from exc

        return ChatGroq(
            model_name=resolved_model,
            groq_api_key=resolved_key,
            temperature=resolved_temp,
            **kwargs,
        )

    # --------------------------------------------------------------------------
    # 3. Invalid / Unsupported Provider
    # --------------------------------------------------------------------------
    else:
        raise LLMConfigError(
            f"Unsupported LLM_PROVIDER: '{resolved_provider}'. "
            f"Supported providers are: '{LLMProvider.OLLAMA.value}' (local development) "
            f"and '{LLMProvider.GROQ.value}' (public deployment). "
            f"Silent fallback is prohibited; please configure a valid provider."
        )
