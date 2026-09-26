# MinIO S3 Object Storage

## Purpose
High-performance S3-compatible object storage serving as the central Data Lake store.

## Buckets Structure
- `raw-data/`: Unprocessed JSON/CSV payloads from scrapers and MQTT ingesters.
- `curated-data/`: Processed, partitioned Parquet datasets ready for BI/analytics.
- `app-assets/`: Media and persistent blob assets.

## Deployment Target
Deploys to **8GB Platform VM** via `infra/platform/docker-compose.yml`.
