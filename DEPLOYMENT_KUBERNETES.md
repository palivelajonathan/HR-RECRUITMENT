# Kubernetes Production Deployment Architecture
**Project**: Recruitment Intelligence Agent  
**Track**: CAPABL Track 6 — HR / Recruitment  
**Milestone**: M8 Hardening & Deployment Readiness  
**Status**: PRODUCTION READY & VALIDATED  

---

## 1. Kubernetes Architecture Overview

For enterprise deployments requiring persistent vector store indexes, secure multi-tenant ingress, and zero-downtime rolling upgrades, the system is designed to deploy on Kubernetes:

```
[ Ingress Controller (NGINX / ALB with TLS termination) ]
                         |
                         v
          [ recruitment-agent-service (ClusterIP:80 -> 8501) ]
                         |
                         v
          [ Pod: agent-app (Replica: 1, Recreate Strategy) ]
                         |
         +---------------+---------------+
         |                               |
         v                               v
[ PVC: chroma-pvc (10Gi RWO) ]   [ PVC: documents-pvc (10Gi RWO) ]
         |
         v
[ Internal Service: ollama-service (DaemonSet / StatefulSet) ]
  OR External Groq API (via Secret: recruitment-agent-secrets)
```

---

## 2. Production Invariants & Hardening Specifications

### 2.1 ChromaDB SQLite Single-Writer Persistence Contract
- **Hard Invariant**: `replicas: 1`
- **Deployment Strategy**: `strategy.type: Recreate`
- **Rationale**: ChromaDB uses an embedded SQLite database and local HNSW index files on disk. Running multiple concurrent pod replicas writing to the same filesystem causes SQLite database locking (`sqlite3.OperationalError: database is locked`) and index corruption. If scaling is needed, read replicas or hosted vector DB architectures must be used.

### 2.2 Pod Security Context (Least Privilege)
The pod and container security contexts enforce strict non-root execution:
```yaml
securityContext:
  runAsNonRoot: true
  runAsUser: 10001
  runAsGroup: 10001
  fsGroup: 10001
containers:
  - name: agent-ui
    securityContext:
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: false
      capabilities:
        drop:
          - ALL
```

### 2.3 Resource Allocations & Limits
```yaml
resources:
  requests:
    cpu: "500m"
    memory: "1Gi"
  limits:
    cpu: "2000m"
    memory: "4Gi"
```

### 2.4 Health & Liveness Probes
- **Readiness Probe**: Queries `GET /_stcore/health` on port 8501 every 10s (initial delay 15s). Pod is only added to Service endpoints once Streamlit, dependencies, and vector stores are ready.
- **Liveness Probe**: Queries `GET /_stcore/health` on port 8501 every 15s (initial delay 30s). Restarts the container if the process hangs.

### 2.5 Ingress & TLS Readiness
- **WebSocket Support**: Streamlit requires persistent WebSocket connections. Ingress annotations configure proxy read/send timeouts (3600s) and WebSocket forwarding:
  ```yaml
  annotations:
    nginx.ingress.kubernetes.io/proxy-read-timeout: "3600"
    nginx.ingress.kubernetes.io/proxy-send-timeout: "3600"
    nginx.ingress.kubernetes.io/websocket-services: "recruitment-agent-service"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
  ```
- **TLS Termination**: Ingress terminates TLS using Secret `recruitment-agent-tls` for domain `recruitment.capabl.local`.

---

## 3. Step-by-Step Deployment Procedure

### Step 3.1: Create Namespace
```bash
kubectl create namespace recruitment-ai
```

### Step 3.2: Configure ConfigMap & Secrets
```bash
# Apply ConfigMap with production settings & resource limits
kubectl apply -f infra/k8s/base/configmap.yaml -n recruitment-ai

# Apply Secret (populate GROQ_API_KEY if deploying with Groq provider)
kubectl apply -f infra/k8s/base/secret.yaml -n recruitment-ai
```

### Step 3.3: Provision Persistent Volume Claims
```bash
kubectl apply -f infra/k8s/base/pvc.yaml -n recruitment-ai

# Verify PVCs are Bound
kubectl get pvc -n recruitment-ai
```

### Step 3.4: Deploy Service & Deployment
```bash
kubectl apply -f infra/k8s/base/service.yaml -n recruitment-ai
kubectl apply -f infra/k8s/base/deployment.yaml -n recruitment-ai

# Verify rollout status
kubectl rollout status deployment/recruitment-agent-app -n recruitment-ai
```

### Step 3.5: Apply Ingress
```bash
kubectl apply -f infra/k8s/base/ingress.yaml -n recruitment-ai
```

---

## 4. Disaster Recovery & Maintenance

### 4.1 Pod Log Streaming
```bash
kubectl logs -f -l app=recruitment-agent-app -n recruitment-ai
```

### 4.2 Safe Vector Store Backup in Kubernetes
Execute backup within the running pod:
```bash
kubectl exec -it deployment/recruitment-agent-app -n recruitment-ai -- python -c "
from capabl_core.rag.persistence import create_chroma_backup
create_chroma_backup('/app/data/chroma_db', '/app/data/resumes/chroma_backup.tar.gz')
print('Backup complete.')
"
kubectl cp recruitment-ai/<pod-name>:/app/data/resumes/chroma_backup.tar.gz ./chroma_backup.tar.gz
```

### 4.3 Safe Vector Store Restore in Kubernetes
```bash
kubectl scale deployment/recruitment-agent-app --replicas=0 -n recruitment-ai
# Mount volume, extract backup.tar.gz, then restart:
kubectl scale deployment/recruitment-agent-app --replicas=1 -n recruitment-ai
```

### 4.4 Rollback on Incident
```bash
kubectl rollout undo deployment/recruitment-agent-app -n recruitment-ai
```
