# Homelab Data Platform

A modular personal data platform designed to run efficiently on small home server hardware. Aggregates data from diverse small services (bus seat scraper, balcony irrigation over MQTT, Android health stats) into a central MinIO S3 data lake, backed by Postgres, Keycloak IAM, Apache Airflow pipeline orchestration, and Grafana monitoring.

---

## Architecture Overview

The system is deployed across two local servers:

- **8GB RAM — "Platform VM"**: Stateful & shared core services: Postgres DB, MinIO S3, Mosquitto MQTT, Apache Airflow, Prometheus + Loki + Grafana, Local Docker Registry (`:5000`), and GitHub Actions self-hosted build runner.
- **4GB RAM — "App VM"**: Lightweight application services: FastAPI Backend, Next.js Frontend, Keycloak IAM, Bus Scraper, Android Health Ingester, and Balcony Irrigation MQTT Client.

> **Key Design Rule**: To avoid memory spikes and OOM kills on the 4GB App VM, **all Docker builds run exclusively on the 8GB Platform VM**. The 4GB box only pulls pre-built images over the LAN.

For detailed design specifications, see [docs/architecture.md](file:///docs/architecture.md).

---

## Directory Layout

```
homelab/
├── .github/
│   └── workflows/
│       ├── ci.yml                    # PR lint & build check (path-filtered, concurrency=1)
│       ├── deploy-platform.yml       # Push to master: builds & deploys to 8GB VM locally
│       └── deploy-apps.yml           # Push to master: builds & SSH deploys to 4GB VM
│
├── services/
│   ├── platform/                     # Platform services (8GB VM)
│   │   ├── airflow/                  # Airflow pipeline orchestration
│   │   ├── minio/                    # S3 object storage fragment
│   │   └── mqtt-broker/              # Eclipse Mosquitto config
│   │
│   └── apps/                         # App services (4GB VM)
│       ├── backend/                  # Python FastAPI API
│       ├── frontend/                 # Next.js web dashboard
│       ├── iam-keycloak/             # Keycloak realm configs
│       ├── bus-scraper/              # RedBus Pune -> Indore scraper
│       ├── health-ingester/          # Android health stats ingester
│       └── irrigation-mqtt/          # Balcony irrigation MQTT client
│
├── infra/
│   ├── platform/                     # docker-compose.yml for 8GB VM
│   ├── apps/                         # docker-compose.yml for 4GB VM
│   └── monitoring/                   # Prometheus, Loki, & Grafana configs
│
├── libs/                             # Shared code across services
│   └── common-python/                # Shared MQTT, logging, and S3 data-lake helpers
│
├── docs/
│   ├── architecture.md               # System topology & GHA CI/CD flow
│   └── rightsizing.md                # RAM/CPU observation log
│
└── README.md
```

---

## How to Add a New Service

When creating a new service (e.g. `services/apps/my-new-ingester`):

1. **Create Directory**: Place the service under `services/apps/<name>/` (for App VM) or `services/platform/<name>/` (for Platform VM).
2. **Add Ownership Files**:
   - `Dockerfile`: Multi-stage or slim Docker build instructions.
   - Dependency manifest (`requirements.txt` or `package.json`).
   - `.env.example`: Sample environment variables.
   - `migrations/`: Service-specific SQL or Alembic migration scripts.
   - `README.md`: Explaining purpose and endpoints.
3. **Register in Docker Compose**: Add the service to `infra/apps/docker-compose.yml` or `infra/platform/docker-compose.yml` referencing `${REGISTRY_HOST:-192.168.1.10:5000}/my-new-ingester:${TAG:-latest}`.
4. **Update GitHub Workflows**: Add path filters to `.github/workflows/ci.yml` and `.github/workflows/deploy-apps.yml`.

---

## Running Locally

### 1. Platform Infrastructure (8GB VM)
```bash
cd infra/platform
cp .env.example .env
docker compose pull && docker compose up -d
```

### 2. App Infrastructure (4GB VM)
```bash
cd infra/apps
cp .env.example .env
docker compose pull && docker compose up -d
```
