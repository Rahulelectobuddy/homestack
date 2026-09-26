# Bus Scraper Service

## Purpose
An automated Playwright-based scraper that extracts bus availability, pricing, timing, and seat configuration (e.g. Pune -> Indore route) on a scheduled basis (every 3 hours by default).

## Directory Structure
- `src/`: Core Python scraping scripts (`cli.py`, `config.py`, `scraper.py`, `exporter.py`, `entrypoint.sh`).
- `migrations/`: Service-specific schema migration scripts if storing state in Postgres.
- `Dockerfile`: Container image build instructions targeting Playwright + Firefox.
- `.env.example`: Service environment variables.

## Deployment Target
Deploys to the **4GB App VM**. Image is built on the 8GB Platform VM during CI and pushed to the local Docker registry.
