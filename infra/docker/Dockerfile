# ==============================================================================
# Dockerfile: Recruitment Intelligence Agent
# Hardened, non-root production container for Streamlit + LangChain runtime
# ==============================================================================

FROM python:3.10-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    APP_ENV=production \
    STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0

WORKDIR /app

# Install minimal system dependencies required for native extensions and health checks
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create dedicated non-root application user and group (UID/GID 10001)
RUN groupadd -g 10001 appuser && \
    useradd -u 10001 -g appuser -s /bin/sh -m appuser

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create runtime directories for Chroma and Audit logging with non-root ownership
RUN mkdir -p /app/data/chroma_db /app/data/resumes /app/data/job_descriptions /app/logs/audit /app/data/sample && \
    chown -R appuser:appuser /app

# Copy application code with non-root ownership
COPY --chown=appuser:appuser capabl_core/ ./capabl_core/
COPY --chown=appuser:appuser enhancement/ ./enhancement/
COPY --chown=appuser:appuser data/sample/ ./data/sample/

# Switch to non-root execution
USER appuser

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
  CMD curl --fail http://localhost:8501/_stcore/health || exit 1

ENTRYPOINT ["streamlit", "run", "capabl_core/ui/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
