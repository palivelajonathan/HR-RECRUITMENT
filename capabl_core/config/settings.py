"""
Centralized Production Configuration & Environment Hardening Subsystem.

CAPABL Track 6 Requirement:
- Single clearly defined production configuration layer.
- Environment variables only for secrets and configuration.
- Strict environment categorization: development, test, production.
- Fail-fast validation at startup (e.g. required Groq key in production).
- Zero hardcoded secrets, passwords, or production URLs.
- Sensible and configurable resource limits.
"""

import os
from enum import Enum
from pathlib import Path
from typing import Optional, Dict, Any, Literal
from pydantic import BaseModel, Field, model_validator
from dotenv import load_dotenv

# Ensure local .env is loaded if present
load_dotenv()


class AppEnvironment(str, Enum):
    """Execution environment mode."""
    DEVELOPMENT = "development"
    TEST = "test"
    PRODUCTION = "production"


class ProductionSettings(BaseModel):
    """
    Strongly typed, validated application configuration schema.
    Serves as the single source of truth across all CAPABL subsystems.
    """

    # --- Environment & Provider Identity ---
    app_env: AppEnvironment = Field(
        default=AppEnvironment.DEVELOPMENT,
        description="Target runtime environment (development, test, production)",
    )
    llm_provider: Literal["ollama", "groq"] = Field(
        default="ollama",
        description="Active LLM provider: 'ollama' for local inference or 'groq' for cloud",
    )

    # --- Ollama Configuration (CAPABL Core Required) ---
    ollama_model: str = Field(
        default="qwen3:8b",
        description="Ollama model identifier (default: qwen3:8b)",
    )
    ollama_base_url: str = Field(
        default="http://localhost:11434",
        description="HTTP endpoint for local Ollama service",
    )
    ollama_temperature: float = Field(
        default=0.1,
        ge=0.0,
        le=1.0,
        description="Sampling temperature for Ollama generation",
    )
    ollama_request_timeout: int = Field(
        default=120,
        ge=5,
        le=600,
        description="HTTP request timeout in seconds for Ollama calls",
    )

    # --- Groq Configuration (Public Cloud Deployment) ---
    groq_api_key: Optional[str] = Field(
        default=None,
        description="API key for Groq Cloud inference (never commit to version control)",
    )
    groq_model: str = Field(
        default="llama-3.3-70b-versatile",
        description="Groq hosted model identifier",
    )
    groq_temperature: float = Field(
        default=0.1,
        ge=0.0,
        le=1.0,
        description="Sampling temperature for Groq generation",
    )

    # --- Storage & Vector Database (Chroma) ---
    chroma_persist_directory: str = Field(
        default="./data/chroma_db",
        description="Local directory for persistent ChromaDB storage",
    )
    chroma_collection_name: str = Field(
        default="recruitment_resumes",
        description="Target collection name in Chroma",
    )
    embedding_model_name: str = Field(
        default="BAAI/bge-small-en-v1.5",
        description="HuggingFace embedding model name",
    )

    # --- Observability & Audit Logging ---
    audit_log_dir: str = Field(
        default="./logs/audit",
        description="Directory where append-only JSONL audit logs reside",
    )
    audit_log_path: str = Field(
        default="./logs/audit/audit_trail.jsonl",
        description="Full path to the audit trail log file",
    )
    audit_max_bytes: int = Field(
        default=10 * 1024 * 1024,  # 10 MB
        ge=1024 * 1024,
        description="Maximum file size before rotating audit log",
    )
    audit_backup_count: int = Field(
        default=5,
        ge=1,
        le=50,
        description="Number of rotated backup log files to retain",
    )
    log_level: str = Field(
        default="INFO",
        description="Standard logging severity level (DEBUG, INFO, WARNING, ERROR)",
    )

    # --- Resource & Security Limits ---
    max_upload_size_mb: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Maximum allowed PDF upload size in megabytes",
    )
    max_pdf_pages: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Maximum allowed page count per ingested PDF document",
    )
    max_document_chunks: int = Field(
        default=100,
        ge=1,
        le=500,
        description="Maximum chunk ceiling allowed per indexed document",
    )
    max_query_length: int = Field(
        default=1000,
        ge=10,
        le=5000,
        description="Maximum character length allowed for recruiter query prompts",
    )
    llm_timeout_seconds: int = Field(
        default=60,
        ge=5,
        le=300,
        description="Per-turn agent reasoning and tool invocation timeout in seconds",
    )

    @model_validator(mode="after")
    def validate_environment_contracts(self) -> "ProductionSettings":
        """Enforces security boundaries based on environment and provider selection."""
        # Clean paths
        self.chroma_persist_directory = str(Path(self.chroma_persist_directory).resolve())
        self.audit_log_dir = str(Path(self.audit_log_dir).resolve())
        self.audit_log_path = str(Path(self.audit_log_path).resolve())

        # Production Groq validation
        if self.llm_provider == "groq":
            if not self.groq_api_key or self.groq_api_key.startswith("placeholder"):
                if self.app_env == AppEnvironment.PRODUCTION:
                    raise ValueError(
                        "Production environment with LLM_PROVIDER='groq' requires a valid, "
                        "non-placeholder GROQ_API_KEY."
                    )
        elif self.llm_provider == "ollama":
            if not self.ollama_base_url or not self.ollama_base_url.startswith(("http://", "https://")):
                raise ValueError(
                    f"LLM_PROVIDER='ollama' requires a valid HTTP base URL, received: '{self.ollama_base_url}'"
                )

        return self

    def get_masked_repr(self) -> Dict[str, Any]:
        """Returns dictionary representation with all secrets safely redacted."""
        data = self.model_dump()
        if data.get("groq_api_key"):
            data["groq_api_key"] = "[REDACTED_SECRET]"
        return data

    def __repr__(self) -> str:
        masked = self.get_masked_repr()
        return f"ProductionSettings({masked})"

    def __str__(self) -> str:
        return self.__repr__()


_CACHED_SETTINGS: Optional[ProductionSettings] = None


def load_settings_from_env() -> ProductionSettings:
    """
    Constructs a ProductionSettings instance parsing active environment variables.
    Provides safe defaults for development and strict validation for production.
    """
    raw_env = os.getenv("APP_ENV", "development").strip().lower()
    try:
        app_env = AppEnvironment(raw_env)
    except ValueError:
        app_env = AppEnvironment.DEVELOPMENT

    provider_str = os.getenv("LLM_PROVIDER", "ollama").strip().lower()
    if provider_str not in ("ollama", "groq"):
        provider_str = "ollama"

    return ProductionSettings(
        app_env=app_env,
        llm_provider=provider_str,  # type: ignore[arg-type]
        ollama_model=os.getenv("OLLAMA_MODEL", "qwen3:8b").strip(),
        ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").strip(),
        ollama_temperature=float(os.getenv("OLLAMA_TEMPERATURE", "0.1")),
        ollama_request_timeout=int(os.getenv("OLLAMA_REQUEST_TIMEOUT", "120")),
        groq_api_key=os.getenv("GROQ_API_KEY", "").strip() or None,
        groq_model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile").strip(),
        groq_temperature=float(os.getenv("GROQ_TEMPERATURE", "0.1")),
        chroma_persist_directory=os.getenv("CHROMA_PERSIST_DIRECTORY", "./data/chroma_db").strip(),
        chroma_collection_name=os.getenv("CHROMA_COLLECTION_NAME", "recruitment_resumes").strip(),
        embedding_model_name=os.getenv("EMBEDDING_MODEL_NAME", "BAAI/bge-small-en-v1.5").strip(),
        audit_log_dir=os.getenv("ENHANCEMENT_AUDIT_LOG_DIR", "./logs/audit").strip(),
        audit_log_path=os.getenv("AUDIT_LOG_PATH", "./logs/audit/audit_trail.jsonl").strip(),
        audit_max_bytes=int(os.getenv("AUDIT_MAX_BYTES", str(10 * 1024 * 1024))),
        audit_backup_count=int(os.getenv("AUDIT_BACKUP_COUNT", "5")),
        log_level=os.getenv("LOG_LEVEL", "INFO").strip().upper(),
        max_upload_size_mb=int(os.getenv("MAX_UPLOAD_SIZE_MB", "10")),
        max_pdf_pages=int(os.getenv("MAX_PDF_PAGES", "20")),
        max_document_chunks=int(os.getenv("MAX_DOCUMENT_CHUNKS", "100")),
        max_query_length=int(os.getenv("MAX_QUERY_LENGTH", "1000")),
        llm_timeout_seconds=int(os.getenv("LLM_TIMEOUT_SECONDS", "60")),
    )


def get_settings() -> ProductionSettings:
    """Returns the cached singleton ProductionSettings instance."""
    global _CACHED_SETTINGS
    if _CACHED_SETTINGS is None:
        _CACHED_SETTINGS = load_settings_from_env()
    return _CACHED_SETTINGS


def reset_settings() -> None:
    """Resets the cached settings singleton (used for hermetic unit testing)."""
    global _CACHED_SETTINGS
    _CACHED_SETTINGS = None
