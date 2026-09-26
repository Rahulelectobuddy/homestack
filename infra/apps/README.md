# App VM Infrastructure (`4GB RAM`)

## Services Hosted
- Backend REST API (`:8000`)
- Frontend Web App (`:3000`)
- Keycloak IAM (`:8080`)
- Bus Scraper Service
- Health Stats Ingester (`:8001`)
- Balcony Irrigation MQTT Client

## Constraints
- **NO Docker builds occur on this VM** to prevent RAM spikes and OOM kills.
- Images are pre-built on the 8GB Platform VM during CI/CD, pushed to the local registry, and pulled over LAN by this VM.

## Deployment Trigger
Automated via SSH deployment step in `.github/workflows/deploy-apps.yml`.
