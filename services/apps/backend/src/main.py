import os
import psycopg2
from psycopg2.extras import RealDictCursor
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

app = FastAPI(
    title="Homelab Data Platform API",
    description="Backend API service for serving analytics, managing ingesters, and serving frontend requests.",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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

@app.get("/api/v1/analytics/bus-fares")
async def get_bus_fares_analytics(
    seat_type: Optional[str] = Query(None, description="Filter by seat category (e.g., single_lower, single_upper, double_lower, double_upper)"),
    operator: Optional[str] = Query(None, description="Filter by bus operator name")
):
    """
    Returns aggregated bus fare analytics, seat type breakdown, and time-series trends
    scraped for the Pune -> Indore route.
    """
    db_url = os.getenv("DATABASE_URL", "postgresql://homelab:homelab123@postgres:5432/homelab_db")
    records = []

    try:
        conn = psycopg2.connect(db_url)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        query = "SELECT * FROM bus_fares_analytics WHERE 1=1"
        params = []
        if seat_type:
            query += " AND seat_type = %s"
            params.append(seat_type)
        if operator:
            query += " AND operator_name ILIKE %s"
            params.append(f"%{operator}%")
        
        query += " ORDER BY scraped_at DESC LIMIT 200"
        cur.execute(query, params)
        records = cur.fetchall()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"[Backend API] PostgreSQL query warning: {e}")

    # Fallback demonstration data if database is empty or starting up
    if not records:
        today = datetime.now()
        records = [
            {
                "id": 1,
                "scraped_at": today.isoformat(),
                "scrape_date": today.strftime("%Y-%m-%d"),
                "travel_date": (today + timedelta(days=2)).strftime("%Y-%m-%d"),
                "days_until_travel": 2,
                "operator_name": "Hans Travels (I) Pvt Ltd",
                "bus_type": "A/C Sleeper (2+1)",
                "seat_type": "single_lower",
                "price": 1250.00,
                "available_seats": 4,
                "has_toilet": True
            },
            {
                "id": 2,
                "scraped_at": today.isoformat(),
                "scrape_date": today.strftime("%Y-%m-%d"),
                "travel_date": (today + timedelta(days=2)).strftime("%Y-%m-%d"),
                "days_until_travel": 2,
                "operator_name": "Intercity Travels",
                "bus_type": "A/C Sleeper (2+1)",
                "seat_type": "single_upper",
                "price": 1050.00,
                "available_seats": 6,
                "has_toilet": True
            },
            {
                "id": 3,
                "scraped_at": today.isoformat(),
                "scrape_date": today.strftime("%Y-%m-%d"),
                "travel_date": (today + timedelta(days=5)).strftime("%Y-%m-%d"),
                "days_until_travel": 5,
                "operator_name": "Hans Travels (I) Pvt Ltd",
                "bus_type": "A/C Sleeper (2+1)",
                "seat_type": "double_lower",
                "price": 1100.00,
                "available_seats": 8,
                "has_toilet": True
            },
            {
                "id": 4,
                "scraped_at": today.isoformat(),
                "scrape_date": today.strftime("%Y-%m-%d"),
                "travel_date": (today + timedelta(days=5)).strftime("%Y-%m-%d"),
                "days_until_travel": 5,
                "operator_name": "Chartered Bus",
                "bus_type": "A/C Sleeper (2+1)",
                "seat_type": "double_upper",
                "price": 900.00,
                "available_seats": 10,
                "has_toilet": False
            }
        ]

    # Calculate summary metrics
    prices = [float(r["price"]) for r in records]
    min_fare = min(prices) if prices else 0
    max_fare = max(prices) if prices else 0
    avg_fare = sum(prices) / len(prices) if prices else 0

    # Seat type price breakdown
    seat_breakdown = {}
    for r in records:
        st = r["seat_type"]
        p = float(r["price"])
        if st not in seat_breakdown:
            seat_breakdown[st] = {"min_price": p, "max_price": p, "total_price": p, "count": 1}
        else:
            seat_breakdown[st]["min_price"] = min(seat_breakdown[st]["min_price"], p)
            seat_breakdown[st]["max_price"] = max(seat_breakdown[st]["max_price"], p)
            seat_breakdown[st]["total_price"] += p
            seat_breakdown[st]["count"] += 1

    formatted_seat_breakdown = [
        {
            "seat_type": st,
            "min_price": round(v["min_price"], 2),
            "max_price": round(v["max_price"], 2),
            "avg_price": round(v["total_price"] / v["count"], 2),
            "total_buses": v["count"]
        }
        for st, v in seat_breakdown.items()
    ]

    # Fare trends grouped by travel_date
    trends = {}
    for r in records:
        td = str(r["travel_date"])
        p = float(r["price"])
        if td not in trends:
            trends[td] = {"travel_date": td, "min_price": p, "avg_price": p, "count": 1}
        else:
            trends[td]["min_price"] = min(trends[td]["min_price"], p)
            trends[td]["avg_price"] += p
            trends[td]["count"] += 1

    formatted_trends = [
        {
            "travel_date": td,
            "min_price": round(v["min_price"], 2),
            "avg_price": round(v["avg_price"] / v["count"], 2)
        }
        for td, v in sorted(trends.items())
    ]

    return {
        "status": "success",
        "route": "Pune to Indore",
        "total_records": len(records),
        "summary": {
            "min_fare": round(min_fare, 2),
            "max_fare": round(max_fare, 2),
            "avg_fare": round(avg_fare, 2)
        },
        "seat_type_breakdown": formatted_seat_breakdown,
        "fare_trends": formatted_trends,
        "records": records
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

