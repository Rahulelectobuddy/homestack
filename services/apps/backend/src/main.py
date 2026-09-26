import os
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(
    title="Homelab Data Platform API",
    description="Backend API service for serving analytics, managing ingesters, and serving frontend requests.",
    version="0.1.0"
)

class HealthResponse(BaseModel):
    status: str
    service: str
    version: str

@app.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="healthy",
        service="backend",
        version="0.1.0"
    )

@app.get("/api/v1/status")
async def get_system_status():
    return {
        "status": "online",
        "environment": os.getenv("APP_ENV", "development"),
        "postgres_connected": True,
        "data_lake_connected": True
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
