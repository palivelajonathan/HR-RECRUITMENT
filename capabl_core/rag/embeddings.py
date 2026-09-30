"""
Embedding Model Subsystem.

CAPABL Requirement:
- HuggingFace / BGE local embeddings.
- Default: BAAI/bge-small-en-v1.5.
- Configurable model name via environment variable (EMBEDDING_MODEL_NAME) or argument.
- Zero reliance on paid external embedding APIs.
"""

import os
from typing import Optional, Any
from langchain_core.embeddings import Embeddings

# Global cache for instantiated embedding model
_EMBEDDING_INSTANCE: Optional[Embeddings] = None
_CACHED_MODEL_NAME: Optional[str] = None


def get_embedding_function(
    model_name: Optional[str] = None,
    device: Optional[str] = None,
    **kwargs: Any,
) -> Embeddings:
    """
    Constructs or returns a cached HuggingFace/BGE Embeddings instance.

    Args:
        model_name: Model identifier (defaults to BAAI/bge-small-en-v1.5 or EMBEDDING_MODEL_NAME env var).
        device: Device to run embeddings on ('cpu', 'cuda', etc.). Defaults to auto-detection.
        **kwargs: Additional parameters passed to the embedding constructor.

    Returns:
        Embeddings: LangChain-compatible embedding object.
    """
    global _EMBEDDING_INSTANCE, _CACHED_MODEL_NAME

    if not model_name:
        try:
            from capabl_core.config.settings import get_settings
            resolved_model = get_settings().embedding_model_name
        except Exception:
            resolved_model = os.getenv("EMBEDDING_MODEL_NAME", "BAAI/bge-small-en-v1.5").strip()
    else:
        resolved_model = model_name.strip()

    # Return cached instance if model has not changed
    if _EMBEDDING_INSTANCE is not None and _CACHED_MODEL_NAME == resolved_model:
        return _EMBEDDING_INSTANCE

    # Try official langchain_huggingface first, fallback to langchain_community
    try:
        from langchain_huggingface import HuggingFaceEmbeddings

        model_kwargs = {"device": device} if device else {}
        encode_kwargs = {"normalize_embeddings": True}

        instance = HuggingFaceEmbeddings(
            model_name=resolved_model,
            model_kwargs=model_kwargs,
            encode_kwargs=encode_kwargs,
            **kwargs,
        )
    except ImportError:
        try:
            from langchain_community.embeddings import HuggingFaceBgeEmbeddings

            model_kwargs = {"device": device} if device else {}
            encode_kwargs = {"normalize_embeddings": True}

            instance = HuggingFaceBgeEmbeddings(
                model_name=resolved_model,
                model_kwargs=model_kwargs,
                encode_kwargs=encode_kwargs,
                **kwargs,
            )
        except ImportError as exc:
            raise ImportError(
                "Neither 'langchain_huggingface' nor 'langchain_community.embeddings' is available. "
                "Please ensure dependencies in requirements.txt are installed."
            ) from exc

    _EMBEDDING_INSTANCE = instance
    _CACHED_MODEL_NAME = resolved_model
    return instance
