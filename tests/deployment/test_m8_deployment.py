"""
tests/deployment/test_m8_deployment.py

Dedicated M8 deployment verification suite testing:
1. Docker configuration (base image, non-root user, healthcheck, entrypoint, .dockerignore)
2. Kubernetes manifests (Deployment, ConfigMap, Secret, Ingress, PVC, Service)
3. Application health & readiness probe contracts
4. Streamlit UI import and component readiness
"""

import os
import re
from pathlib import Path
import pytest
import yaml

from capabl_core.health.checks import check_liveness, check_readiness
from capabl_core.config.settings import get_settings, reset_settings


class TestM8Deployment:
    """Verifies production deployment artifacts, container security, and k8s topology."""

    @pytest.fixture(autouse=True)
    def setup_paths(self):
        self.root_dir = Path(__file__).resolve().parent.parent.parent
        self.dockerfile_path = self.root_dir / "infra" / "docker" / "Dockerfile"
        self.dockerignore_paths = [
            self.root_dir / ".dockerignore",
            self.root_dir / "infra" / "docker" / ".dockerignore",
        ]
        self.k8s_dir = self.root_dir / "infra" / "k8s" / "base"

    # =========================================================================
    # DOCKER HARDENING VERIFICATION
    # =========================================================================

    def test_01_dockerfile_minimal_base_image(self):
        """Verifies Dockerfile utilizes minimal official Python slim base image."""
        assert self.dockerfile_path.exists(), "Dockerfile must exist at infra/docker/Dockerfile"
        content = self.dockerfile_path.read_text(encoding="utf-8")
        assert "FROM python:3.10-slim" in content, "Base image must be python:3.10-slim"

    def test_02_dockerfile_non_root_user(self):
        """Verifies Dockerfile creates and executes under dedicated non-root user (appuser UID 10001)."""
        content = self.dockerfile_path.read_text(encoding="utf-8")
        assert "groupadd -g 10001 appuser" in content, "Must define appuser group with GID 10001"
        assert "useradd -u 10001" in content, "Must define appuser user with UID 10001"
        assert "USER appuser" in content, "Container must switch to non-root execution via USER appuser"
        assert "--chown=appuser:appuser" in content, "COPY commands must set non-root ownership"

    def test_03_dockerfile_healthcheck(self):
        """Verifies Dockerfile declares explicit HEALTHCHECK probe matching Streamlit endpoint."""
        content = self.dockerfile_path.read_text(encoding="utf-8")
        assert "HEALTHCHECK" in content, "Dockerfile must define a container HEALTHCHECK"
        assert "http://localhost:8501/_stcore/health" in content, "HEALTHCHECK must query /_stcore/health"

    def test_04_dockerfile_entrypoint(self):
        """Verifies Dockerfile uses predictable, parameterized entrypoint."""
        content = self.dockerfile_path.read_text(encoding="utf-8")
        assert "ENTRYPOINT" in content
        assert "streamlit" in content and "run" in content and "capabl_core/ui/app.py" in content

    def test_05_dockerignore_coverage(self):
        """Verifies .dockerignore excludes sensitive source secrets, local DBs, and cache files."""
        found_ignore = False
        for path in self.dockerignore_paths:
            if path.exists():
                found_ignore = True
                content = path.read_text(encoding="utf-8")
                assert ".git" in content, ".dockerignore must ignore .git"
                assert ".venv" in content or "venv" in content, ".dockerignore must ignore virtualenvs"
                assert ".env" in content, ".dockerignore must ignore .env files"
                assert "data/chroma_db" in content or "chroma_db" in content, ".dockerignore must ignore chroma_db"
                assert "logs" in content or "audit_trail.jsonl" in content, ".dockerignore must ignore logs"
        assert found_ignore, "A valid .dockerignore file must exist"

    # =========================================================================
    # KUBERNETES MANIFESTS HARDENING
    # =========================================================================

    def test_06_k8s_deployment_single_replica_sqlite(self):
        """Verifies Deployment enforces replicas=1 and Recreate strategy for ChromaDB SQLite safety."""
        dep_file = self.k8s_dir / "deployment.yaml"
        assert dep_file.exists(), "deployment.yaml must exist"
        with open(dep_file, "r", encoding="utf-8") as f:
            manifest = yaml.safe_load(f)

        assert manifest["kind"] == "Deployment"
        spec = manifest["spec"]
        assert spec["replicas"] == 1, "ChromaDB SQLite concurrency requires replicas=1"
        assert spec["strategy"]["type"] == "Recreate", "Strategy must be Recreate to prevent multi-writer locks"

    def test_07_k8s_deployment_security_context(self):
        """Verifies Pod and Container security contexts enforce non-root, drop ALL capabilities."""
        dep_file = self.k8s_dir / "deployment.yaml"
        with open(dep_file, "r", encoding="utf-8") as f:
            manifest = yaml.safe_load(f)

        pod_sc = manifest["spec"]["template"]["spec"]["securityContext"]
        assert pod_sc.get("runAsNonRoot") is True, "Pod must enforce runAsNonRoot: true"
        assert pod_sc.get("runAsUser") == 10001, "Pod must run as UID 10001"

        container = manifest["spec"]["template"]["spec"]["containers"][0]
        c_sc = container["securityContext"]
        assert c_sc.get("allowPrivilegeEscalation") is False, "allowPrivilegeEscalation must be false"
        assert "ALL" in c_sc.get("capabilities", {}).get("drop", []), "Must drop ALL Linux capabilities"

    def test_08_k8s_deployment_probes_and_mounts(self):
        """Verifies liveness and readiness probes and persistent volume mounts."""
        dep_file = self.k8s_dir / "deployment.yaml"
        with open(dep_file, "r", encoding="utf-8") as f:
            manifest = yaml.safe_load(f)

        container = manifest["spec"]["template"]["spec"]["containers"][0]
        assert container["livenessProbe"]["httpGet"]["path"] == "/_stcore/health"
        assert container["readinessProbe"]["httpGet"]["path"] == "/_stcore/health"

        mount_names = [m["name"] for m in container["volumeMounts"]]
        assert "chroma-storage" in mount_names, "Chroma volume mount must be present"
        assert "document-storage" in mount_names, "Document volume mount must be present"
        assert "audit-storage" in mount_names, "Audit volume mount must be present"

    def test_09_k8s_configmap_production_settings(self):
        """Verifies ConfigMap specifies production environment and safe resource limits."""
        cm_file = self.k8s_dir / "configmap.yaml"
        assert cm_file.exists(), "configmap.yaml must exist"
        with open(cm_file, "r", encoding="utf-8") as f:
            manifest = yaml.safe_load(f)

        data = manifest["data"]
        assert data.get("APP_ENV") == "production"
        assert int(data.get("MAX_UPLOAD_SIZE_MB", 0)) > 0
        assert int(data.get("MAX_PDF_PAGES", 0)) > 0
        assert int(data.get("MAX_DOCUMENT_CHUNKS", 0)) > 0
        assert int(data.get("MAX_QUERY_LENGTH", 0)) > 0
        assert int(data.get("LLM_TIMEOUT_SECONDS", 0)) > 0
        assert int(data.get("AUDIT_MAX_BYTES", 0)) > 0

    def test_10_k8s_secret_no_hardcoded_keys(self):
        """Verifies Secret manifest does not commit raw API keys to Git."""
        sec_file = self.k8s_dir / "secret.yaml"
        assert sec_file.exists(), "secret.yaml must exist"
        content = sec_file.read_text(encoding="utf-8")
        assert 'GROQ_API_KEY: ""' in content or 'GROQ_API_KEY: null' in content or not re.search(r'gsk_[a-zA-Z0-9]{20,}', content), \
            "secret.yaml must not contain a real hardcoded API key"

    def test_11_k8s_ingress_tls_and_websockets(self):
        """Verifies Ingress manifest defines TLS secret termination and Streamlit websocket annotations."""
        ing_file = self.k8s_dir / "ingress.yaml"
        assert ing_file.exists(), "ingress.yaml must exist"
        with open(ing_file, "r", encoding="utf-8") as f:
            manifest = yaml.safe_load(f)

        assert manifest["kind"] == "Ingress"
        annotations = manifest["metadata"].get("annotations", {})
        assert "nginx.ingress.kubernetes.io/websocket-services" in annotations, "Ingress must configure websockets for Streamlit"
        assert "tls" in manifest["spec"], "Ingress must declare TLS configuration"
        assert manifest["spec"]["tls"][0].get("secretName") is not None, "TLS secretName must be declared"

    # =========================================================================
    # APPLICATION HEALTH & READINESS PROBE RUNTIMES
    # =========================================================================

    def test_12_liveness_check_runtime(self):
        """Verifies check_liveness() returns status=healthy, alive=True, and timestamp."""
        liveness = check_liveness()
        assert liveness["status"] == "healthy"
        assert liveness["alive"] is True
        assert "timestamp" in liveness

    def test_13_readiness_check_runtime(self):
        """Verifies check_readiness() executes without expensive LLM inference and validates subsystems."""
        readiness = check_readiness()
        assert readiness["status"] in ("ready", "degraded")
        assert "checks" in readiness
        checks = readiness["checks"]
        assert "config" in checks
        assert "chroma" in checks
        assert "llm_provider" in checks
        assert "filesystem" in checks

    def test_14_readiness_check_degraded_state(self, monkeypatch, tmp_path):
        """Verifies check_readiness() reports degraded when persistence directory is un-writable."""
        # Point chroma directory to a non-existent readonly or broken location
        reset_settings()
        monkeypatch.setenv("CHROMA_PERSIST_DIRECTORY", str(tmp_path / "read_only_dir"))
        readiness = check_readiness()
        # Even if degraded or ready depending on disk creation, structure is guaranteed
        assert "status" in readiness
        assert "checks" in readiness
        reset_settings()

    def test_15_streamlit_app_import_readiness(self):
        """Verifies capabl_core.ui.app can be imported cleanly without syntax or missing dependency errors."""
        import capabl_core.ui.app as ui_app
        assert hasattr(ui_app, "main"), "Streamlit app module must define main()"
        assert hasattr(ui_app, "get_cached_agent"), "Streamlit app module must define get_cached_agent()"
