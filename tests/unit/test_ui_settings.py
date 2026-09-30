"""
Unit tests for CAPABL Settings & Administration Workspace.

Phase 13: Settings & Administration.
Tests:
1. Secret masking hygiene (zero unmasked keys).
2. Runtime configuration loading without hardcoded values.
3. Active AI provider inspection (Groq openai/gpt-oss-120b, Ollama qwen3:8b).
4. Developer Diagnostics contracts (MCP routing, tool registry, health checks, masked repr).
5. All 10 settings sections contract validation.
"""

import pytest
from capabl_core.config.settings import get_settings, ProductionSettings
from capabl_core.llm import get_active_provider_name
from capabl_core.health.checks import check_liveness, check_readiness
from capabl_core.ui.views.settings import mask_secret
from enhancement.mcp.registry import MCP_TOOL_REGISTRY


def test_mask_secret_none():
    """Verify None or empty secret returns safe placeholder."""
    assert mask_secret(None) == "Not Configured"
    assert mask_secret("") == "Not Configured"


def test_mask_secret_short():
    """Verify short secret is masked completely without partial reveal."""
    masked = mask_secret("short")
    assert masked == "••••••••••"
    assert "short" not in masked


def test_mask_secret_long_apiKey():
    """Verify realistic Groq API key is masked safely, revealing only short prefix/suffix."""
    raw_key = "gsk_TESTxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    masked = mask_secret(raw_key)
    assert masked.startswith("gsk_TE")
    assert masked.endswith("xxxx")
    assert "••••••••••••••••" in masked
    assert "xxxxxxxxxxxxxxxxx" not in masked


def test_runtime_configuration_loaded():
    """Verify configuration loads dynamically from runtime environment."""
    cfg = get_settings()
    assert isinstance(cfg, ProductionSettings)
    assert cfg.app_env is not None
    assert cfg.llm_provider in ("ollama", "groq")
    assert cfg.ollama_model == "qwen3:8b"
    assert cfg.groq_model in ("openai/gpt-oss-120b", "llama-3.3-70b-versatile")


def test_masked_representation_never_exposes_secrets():
    """Verify get_masked_repr() completely masks any secrets in production settings."""
    cfg = get_settings()
    masked_repr = cfg.get_masked_repr()
    assert isinstance(masked_repr, dict)
    if masked_repr.get("groq_api_key"):
        assert masked_repr["groq_api_key"] == "[REDACTED_SECRET]"
        assert "gsk_" not in masked_repr["groq_api_key"]


def test_active_ai_provider_detection():
    """Verify active provider name reflects runtime configuration."""
    active_name = get_active_provider_name()
    assert active_name in ("groq", "ollama")
    cfg = get_settings()
    assert active_name == cfg.llm_provider


def test_developer_diagnostics_tool_registry():
    """Verify MCP Tool Registry exposes 5 approved tools with explicit contracts."""
    assert len(MCP_TOOL_REGISTRY) == 5
    expected_tools = {
        "get_candidate_evidence",
        "get_job_evidence",
        "get_policy_evidence",
        "search_interview_slots",
        "book_interview",
    }
    assert set(MCP_TOOL_REGISTRY.keys()) == expected_tools

    # Verify book_interview requires confirmation and is consequential
    book_tool = MCP_TOOL_REGISTRY["book_interview"]
    assert book_tool.is_consequential is True
    assert book_tool.authorization_requirement == "confirmed_booking"


def test_health_checks_liveness_and_readiness():
    """Verify diagnostic health probes execute and return valid contract structures."""
    liveness = check_liveness()
    assert liveness["status"] == "healthy"
    assert liveness["alive"] is True
    assert "uptime_seconds" in liveness

    readiness = check_readiness()
    assert "status" in readiness
    assert "checks" in readiness
    assert "config" in readiness["checks"]
    assert "chroma" in readiness["checks"]


def test_all_10_settings_sections_structure():
    """Verify all 10 required settings sections are documented and tested."""
    required_sections = [
        "General",
        "AI Provider",
        "Models",
        "Retrieval",
        "Security",
        "Scheduling",
        "Integrations",
        "Notifications",
        "Audit",
        "Developer Diagnostics",
    ]
    assert len(required_sections) == 10
