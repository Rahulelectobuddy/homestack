# Agent Instructions & Guidelines for Homelab Data Platform

## Repository Overview
This repository contains a modular personal data platform split across two local servers:
1. **Platform VM (8GB RAM)**: Stateful infrastructure (Postgres, MinIO, Mosquitto MQTT, Airflow, Prometheus, Loki, Grafana, Local Registry).
2. **App VM (4GB RAM)**: Application microservices (FastAPI Backend, Next.js Frontend, Keycloak IAM, Bus Scraper, Health Ingester, Irrigation MQTT Client).

---

## Agent Coding & Architectural Rules

### 1. Zero Build Strategy on App VM
- Never add container build steps or build contexts to `infra/apps/docker-compose.yml`.
- All `docker-compose.yml` entries under `infra/apps/` MUST reference pre-built image tags from the local registry (`REGISTRY_HOST:5000/service:tag`).

### 2. Microservice Isolation & Per-Service Ownership
- Each service in `services/apps/` and `services/platform/` owns its own `Dockerfile`, dependency file (`requirements.txt` / `package.json`), `.env.example`, and `migrations/` directory.
- Database migrations are strictly per-service; do NOT create global shared migration scripts.

### 3. CI/CD Concurrency & Path Filtering Rules
- All GitHub Actions workflows (`.github/workflows/*.yml`) MUST include `paths:` filters targeting only relevant directories.
- Keep `concurrency: 1` on build jobs to protect memory usage on the 8GB Platform VM runner.

### 4. Shared Libraries
- Use `libs/common-python/` for reusable Python modules (`common/mqtt.py`, `common/logging.py`, `common/lake.py`).
- Do not duplicate MQTT or MinIO client logic across services.

---

## Detailed Specifications
Refer to the `.agents/specs/` directory for full specifications:
- [Architecture Spec](file:///.agents/specs/architecture-spec.md)
- [CI/CD Spec](file:///.agents/specs/cicd-spec.md)
- [Services & Data Lake Spec](file:///.agents/specs/services-spec.md)
