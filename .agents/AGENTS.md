# Agent Instructions & Guidelines for Homelab Data Platform

## Repository Overview
This repository contains a modular personal data platform running on a single host (`192.168.1.29`):
1. **Unified Stack**: Stateful infrastructure (Postgres, MinIO, Mosquitto MQTT, Airflow, Prometheus, Loki, Grafana, Local Registry) and application microservices (FastAPI Backend, Next.js Frontend, Keycloak IAM, Bus Scraper, Health Ingester, Irrigation MQTT Client).

---

## Agent Coding & Architectural Rules

### 1. Unified Deployment Strategy
- The primary deployment specification is defined in the root [docker-compose.yml](file:///Users/ritikgarg/workspace/antigravity/homestack/docker-compose.yml).
- Microservices use internal container DNS (`postgres`, `minio`, `mqtt-broker`) for service-to-service communication.

### 2. Microservice Isolation & Per-Service Ownership
- Each service in `services/apps/` and `services/platform/` owns its own `Dockerfile`, dependency file (`requirements.txt` / `package.json`), `.env.example`, and `migrations/` directory.
- Database migrations are strictly per-service; do NOT create global shared migration scripts.

### 3. CI/CD Concurrency & Path Filtering Rules
- GitHub Actions workflow (`.github/workflows/deploy.yml`) builds changed services and deploys the unified stack on host `192.168.1.29`.

### 4. Shared Libraries
- Use `libs/common-python/` for reusable Python modules (`common/mqtt.py`, `common/logging.py`, `common/lake.py`).
- Do not duplicate MQTT or MinIO client logic across services.

---

## Detailed Specifications
Refer to the `.agents/specs/` directory for full specifications:
- [Architecture Spec](file:///.agents/specs/architecture-spec.md)
- [CI/CD Spec](file:///.agents/specs/cicd-spec.md)
- [Services & Data Lake Spec](file:///.agents/specs/services-spec.md)
