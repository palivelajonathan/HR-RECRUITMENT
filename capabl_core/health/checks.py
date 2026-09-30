"""
Application Health, Liveness, and Readiness Probe Subsystem.

CAPABL Track 6 Requirement:
- Separate Liveness ('is process alive') from Readiness ('can process perform operations').
- Readiness verifies LLM provider configuration, Chroma persistence, required directories,
  and configuration contracts without executing expensive LLM generation calls.
- Lightweight, deterministic, and compatible with Kubernetes probes and internal diagnostics.
"""

import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List

from capabl_core.config.settings import get_settings, AppEnvironment
from capabl_core.rag.persistence import verify_chroma_storage_integrity

_PROCESS_START_TIME = time.time()


def check_liveness() -> Dict[str, Any]:
    """
    Lightweight probe evaluating whether the process is alive and responsive.
    Corresponds to Kubernetes livenessProbe.
    """
    uptime = round(time.time() - _PROCESS_START_TIME, 2)
    return {
        "status": "healthy",
        "alive": True,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": uptime,
        "app": "recruitment-intelligence-agent",
    }


def check_readiness() -> Dict[str, Any]:
    """
    Evaluates whether application dependencies and storage layers are operational.
    Corresponds to Kubernetes readinessProbe.
    
    Verifies:
    1. Configuration integrity
    2. Chroma persistence directory access & writability
    3. LLM provider contract readiness (without calling LLM generation)
    4. Essential filesystem directories
    """
    timestamp = datetime.now(timezone.utc).isoformat()
    checks: Dict[str, Any] = {}
    is_ready = True
    messages: List[str] = []

    # 1. Configuration check
    try:
        cfg = get_settings()
        checks["config"] = {
            "status": "pass",
            "app_env": cfg.app_env.value,
            "llm_provider": cfg.llm_provider,
        }
    except Exception as exc:
        is_ready = False
        checks["config"] = {"status": "fail", "error": str(exc)}
        messages.append(f"Configuration failure: {exc}")
        return {
            "status": "not_ready",
            "ready": False,
            "timestamp": timestamp,
            "checks": checks,
            "messages": messages,
        }

    # 2. Chroma storage check
    try:
        chroma_res = verify_chroma_storage_integrity(cfg.chroma_persist_directory)
        if chroma_res.get("healthy"):
            checks["chroma"] = {"status": "pass", "path": chroma_res["path"]}
        else:
            is_ready = False
            checks["chroma"] = {"status": "fail", "message": chroma_res.get("message")}
            messages.append(f"Chroma storage failure: {chroma_res.get('message')}")
    except Exception as exc:
        is_ready = False
        checks["chroma"] = {"status": "fail", "error": str(exc)}
        messages.append(f"Chroma integrity error: {exc}")

    # 3. LLM provider contract check
    if cfg.llm_provider == "ollama":
        if cfg.ollama_base_url and cfg.ollama_model:
            checks["llm_provider"] = {
                "status": "pass",
                "provider": "ollama",
                "model": cfg.ollama_model,
                "base_url": cfg.ollama_base_url,
            }
        else:
            is_ready = False
            checks["llm_provider"] = {"status": "fail", "reason": "Missing Ollama model or base URL"}
            messages.append("Ollama configuration is incomplete.")
    elif cfg.llm_provider == "groq":
        if cfg.groq_api_key and not cfg.groq_api_key.startswith("placeholder"):
            checks["llm_provider"] = {
                "status": "pass",
                "provider": "groq",
                "model": cfg.groq_model,
            }
        else:
            # If in production, missing Groq key is a readiness blocker
            if cfg.app_env == AppEnvironment.PRODUCTION:
                is_ready = False
                checks["llm_provider"] = {"status": "fail", "reason": "Missing GROQ_API_KEY in production"}
                messages.append("GROQ_API_KEY required for production cloud deployment.")
            else:
                checks["llm_provider"] = {
                    "status": "warning",
                    "reason": "GROQ_API_KEY not configured (development mode)",
                }

    # 4. Storage directories check
    dir_failures = []
    for d_path in [Path(cfg.audit_log_dir), Path("./data")]:
        try:
            d_path.mkdir(parents=True, exist_ok=True)
        except Exception as exc:
            dir_failures.append(f"{d_path}: {exc}")

    if dir_failures:
        is_ready = False
        checks["filesystem"] = {"status": "fail", "errors": dir_failures}
        messages.extend(dir_failures)
    else:
        checks["filesystem"] = {"status": "pass"}

    return {
        "status": "ready" if is_ready else "not_ready",
        "ready": is_ready,
        "timestamp": timestamp,
        "checks": checks,
        "messages": messages,
    }
