# Specification: Homelab CI/CD Flow

## Key Mechanics
1. **Runner**: GitHub Actions runner self-hosted on the 8GB Platform VM.
2. **Registry**: Local Docker Registry running on `localhost:5000` on the 8GB Platform VM.
3. **Artifact Tagging**: Every build generates `sha-<commit_hash_7_chars>` and `:latest`.
4. **App VM Deployment**: Triggered via SSH command:
   ```bash
   ssh user@192.168.1.11 "cd /opt/homelab/infra/apps && docker compose pull && docker compose up -d"
   ```

## Path Filters Table

| Changed Directory | Triggered Workflow | Deploy Target |
| :--- | :--- | :--- |
| `services/platform/airflow/**` | `deploy-platform.yml` | Platform VM (Local docker compose) |
| `services/apps/backend/**` | `deploy-apps.yml` | App VM (SSH remote deploy) |
| `services/apps/frontend/**` | `deploy-apps.yml` | App VM (SSH remote deploy) |
| `services/apps/bus-scraper/**` | `deploy-apps.yml` | App VM (SSH remote deploy) |
| `services/apps/health-ingester/**` | `deploy-apps.yml` | App VM (SSH remote deploy) |
| `services/apps/irrigation-mqtt/**` | `deploy-apps.yml` | App VM (SSH remote deploy) |
