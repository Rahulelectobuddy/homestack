# Shared Common Python Library (`homelab-common`)

## Purpose
Reusable Python modules shared across ingestion services, data pipelines, and backend APIs:
- `common/mqtt.py`: MQTT Client wrapper with auto-reconnection and topic routing.
- `common/logging.py`: Structured console logging setup with JSON formatting support.
- `common/lake.py`: MinIO S3 data lake writer enforcing Hive-partitioned directory layout (`raw-data/{dataset}/year=YYYY/month=MM/`).

## Installation in Services
Add to service `Dockerfile` or `requirements.txt`:
```dockerfile
COPY libs/common-python /tmp/common-python
RUN pip install /tmp/common-python
```
