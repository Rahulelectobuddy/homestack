# Specification: Services & Data Lake Schema

## Data Lake Layout (MinIO S3)

MinIO uses Hive-style partition paths:

```
s3://raw-data/
├── bus_scraper/year=2026/month=09/day=26/bus_fares_20260926_120000.csv
├── health_ingester/year=2026/month=09/day=26/steps_batch_001.json
└── irrigation/year=2026/month=09/day=26/soil_moisture.json

s3://curated-data/
├── bus_fares/year=2026/month=09/data.parquet
├── health_stats/year=2026/month=09/data.parquet
└── irrigation_events/year=2026/month=09/data.parquet
```

## Bus Scraper Contract
- Target Route: Pune -> Indore (RedBus).
- Schedule: Every 3 hours via container loop (`entrypoint.sh`).
- Output: Timestamped CSV to `exports/` and MinIO `raw-data/bus_scraper/`.
