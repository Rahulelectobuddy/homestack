import os
import sys
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

app = FastAPI(title="Android Health Stats Ingester", version="0.1.0")

class HealthMetric(BaseModel):
    timestamp: str
    metric_type: str  # e.g., steps, heart_rate, sleep, calories
    value: float
    unit: str
    metadata: Optional[Dict[str, Any]] = None

class BatchHealthDataPayload(BaseModel):
    device_id: str
    metrics: List[HealthMetric]

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "health-ingester"}

@app.post("/api/v1/health-data")
async def ingest_health_data(
    payload: BatchHealthDataPayload, 
    x_api_key: Optional[str] = Header(None)
):
    print(f"Received {len(payload.metrics)} health metrics from device {payload.device_id}")

    s3_path = None
    minio_endpoint = os.getenv("MINIO_ENDPOINT", "")
    if minio_endpoint:
        try:
            from common.lake import DataLakeWriter
            writer = DataLakeWriter(
                minio_endpoint=minio_endpoint,
                access_key=os.getenv("MINIO_ROOT_USER", "minioadmin"),
                secret_key=os.getenv("MINIO_ROOT_PASSWORD", "minioadmin")
            )
            s3_path = writer.write_json(
                bucket="raw-data",
                dataset="health_ingester",
                data=payload.model_dump() if hasattr(payload, 'model_dump') else payload.dict()
            )
            print(f"Pushed health metrics to Data Lake: {s3_path}")
        except Exception as e:
            print(f"Data Lake export error: {e}")

    return {
        "status": "success",
        "ingested_count": len(payload.metrics),
        "s3_path": s3_path
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001)

