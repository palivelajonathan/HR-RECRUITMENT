"""
Milestone 8 Integration Tests: Production Hardening, Health Probes & Disaster Recovery.

CAPABL Track 6 Requirement:
- Verify centralized ProductionSettings validation across environments (dev, test, prod).
- Verify lightweight Liveness and Readiness health probes.
- Verify failure classification (retryable vs non-retryable) and bounded retry logic.
- Verify ChromaDB backup, restore, and storage integrity procedures.
"""

import os
import shutil
import tempfile
from pathlib import Path
import pytest

from capabl_core.config.settings import (
    AppEnvironment,
    ProductionSettings,
    get_settings,
    reset_settings,
    load_settings_from_env,
)
from capabl_core.health.checks import check_liveness, check_readiness
from capabl_core.agent.failure_handler import (
    is_retryable_error,
    execute_with_retry,
)
from capabl_core.rag.persistence import (
    create_chroma_backup,
    restore_chroma_backup,
    verify_chroma_storage_integrity,
)


class TestM8Hardening:
    """Integration test suite for M8 production hardening and recovery."""

    def test_01_production_settings_defaults(self):
        """Verifies default settings load cleanly with safe development defaults."""
        reset_settings()
        cfg = get_settings()
        assert cfg.app_env in (AppEnvironment.DEVELOPMENT, AppEnvironment.TEST, AppEnvironment.PRODUCTION)
        assert cfg.llm_provider in ("ollama", "groq")
        assert cfg.max_upload_size_mb == 10
        assert cfg.max_pdf_pages == 20
        assert cfg.max_document_chunks == 100
        assert cfg.max_query_length == 1000
        assert cfg.llm_timeout_seconds == 60

    def test_02_production_settings_groq_validation(self):
        """Verifies that production mode strictly requires valid GROQ_API_KEY when provider is groq."""
        # Development mode allows missing key
        dev_cfg = ProductionSettings(
            app_env=AppEnvironment.DEVELOPMENT,
            llm_provider="groq",
            groq_api_key=None,
        )
        assert dev_cfg.llm_provider == "groq"

        # Production mode rejects missing or placeholder key
        with pytest.raises(ValueError, match="requires a valid, non-placeholder GROQ_API_KEY"):
            ProductionSettings(
                app_env=AppEnvironment.PRODUCTION,
                llm_provider="groq",
                groq_api_key=None,
            )

        with pytest.raises(ValueError, match="requires a valid, non-placeholder GROQ_API_KEY"):
            ProductionSettings(
                app_env=AppEnvironment.PRODUCTION,
                llm_provider="groq",
                groq_api_key="placeholder-key",
            )

    def test_03_production_settings_masked_representation(self):
        """Verifies that ProductionSettings.__repr__ and get_masked_repr never leak secrets."""
        cfg = ProductionSettings(
            app_env=AppEnvironment.DEVELOPMENT,
            llm_provider="groq",
            groq_api_key="gsk_real_secret_token_1234567890",
        )
        repr_str = repr(cfg)
        assert "gsk_real_secret_token_1234567890" not in repr_str
        assert "[REDACTED_SECRET]" in repr_str
        assert cfg.get_masked_repr()["groq_api_key"] == "[REDACTED_SECRET]"

    def test_04_liveness_probe(self):
        """Verifies that the lightweight liveness probe returns healthy status."""
        live_res = check_liveness()
        assert live_res["status"] == "healthy"
        assert live_res["alive"] is True
        assert live_res["uptime_seconds"] >= 0
        assert "timestamp" in live_res

    def test_05_readiness_probe(self):
        """Verifies that the readiness probe evaluates dependencies without calling LLMs."""
        ready_res = check_readiness()
        assert "status" in ready_res
        assert "ready" in ready_res
        assert "checks" in ready_res
        assert "config" in ready_res["checks"]
        assert "chroma" in ready_res["checks"]
        assert "filesystem" in ready_res["checks"]

    def test_06_failure_classification_retryable(self):
        """Verifies accurate detection of transient retryable exceptions."""
        assert is_retryable_error(ConnectionError("Connection refused by host")) is True
        assert is_retryable_error(TimeoutError("Read timed out")) is True
        assert is_retryable_error(RuntimeError("CUDA out of memory error")) is True
        assert is_retryable_error(Exception("HTTP 429 Rate limit exceeded")) is True

    def test_07_failure_classification_non_retryable(self):
        """Verifies immediate rejection of non-retryable errors without infinite looping."""
        assert is_retryable_error(ValueError("Invalid slot parameter")) is False
        assert is_retryable_error(FileNotFoundError("Missing document")) is False
        assert is_retryable_error(Exception("Confirmation required for booking")) is False
        assert is_retryable_error(Exception("Candidate mismatch detected")) is False
        assert is_retryable_error(Exception("Invalid PDF signature")) is False

    def test_08_bounded_retry_execution(self):
        """Verifies that execute_with_retry successfully retries and returns result."""
        call_count = 0

        def flaky_service():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ConnectionError("Temporary network timeout")
            return "SUCCESS"

        result = execute_with_retry(
            flaky_service,
            max_retries=2,
            initial_delay=0.01,
            backoff_factor=1.0,
            operation_name="test_flaky",
        )
        assert result == "SUCCESS"
        assert call_count == 2

    def test_09_bounded_retry_exhaustion(self):
        """Verifies that execute_with_retry raises after exceeding max retries."""
        attempts = 0

        def failing_service():
            nonlocal attempts
            attempts += 1
            raise ConnectionError("Persistent connection failure")

        with pytest.raises(ConnectionError, match="Persistent connection failure"):
            execute_with_retry(
                failing_service,
                max_retries=2,
                initial_delay=0.01,
                backoff_factor=1.0,
                operation_name="test_failing",
            )
        assert attempts == 3  # initial attempt + 2 retries

    def test_10_chroma_backup_and_restore_cycle(self):
        """
        Verifies deterministic backup, archive creation, and restore cycle
        ensuring zero data loss across restarts.
        """
        temp_dir = tempfile.mkdtemp()
        try:
            # 1. Setup mock Chroma directory
            chroma_src = Path(temp_dir) / "chroma_source"
            chroma_src.mkdir(parents=True)
            mock_sqlite = chroma_src / "chroma.sqlite3"
            mock_sqlite.write_text("MOCK_CHROMA_SQLITE_DATA_12345", encoding="utf-8")

            backup_dest = Path(temp_dir) / "backups"
            backup_dest.mkdir()

            # 2. Execute backup
            archive_path = create_chroma_backup(
                source_dir=chroma_src,
                backup_dest_dir=backup_dest,
            )
            assert archive_path.exists()
            assert archive_path.name.endswith(".tar.gz")

            # 3. Restore into new target
            restore_target = Path(temp_dir) / "chroma_restored"
            restored_path = restore_chroma_backup(
                backup_archive_path=archive_path,
                target_dir=restore_target,
                overwrite=True,
            )
            assert restored_path.exists()
            restored_sqlite = restored_path / "chroma.sqlite3"
            assert restored_sqlite.exists()
            assert restored_sqlite.read_text(encoding="utf-8") == "MOCK_CHROMA_SQLITE_DATA_12345"

            # 4. Verify storage integrity
            integrity = verify_chroma_storage_integrity(restored_path)
            assert integrity["healthy"] is True
            assert integrity["sqlite_exists"] is True
            assert integrity["is_writable"] is True
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
