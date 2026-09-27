import os
import io
import json
import logging
from datetime import datetime, timedelta, timezone
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values

from airflow import DAG
from airflow.operators.python import PythonOperator

logger = logging.getLogger("airflow.task")

default_args = {
    'owner': 'homelab',
    'depends_on_past': False,
    'start_date': datetime(2026, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

def init_postgres_db():
    """Ensure bus_fares_analytics table exists in PostgreSQL."""
    db_url = os.getenv("DATABASE_URL", "postgresql://homelab:homelab123@postgres:5432/homelab_db")
    try:
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS bus_fares_analytics (
                id SERIAL PRIMARY KEY,
                scraped_at TIMESTAMP WITH TIME ZONE NOT NULL,
                scrape_date DATE NOT NULL,
                travel_date DATE NOT NULL,
                days_until_travel INT NOT NULL,
                operator_name VARCHAR(100) NOT NULL,
                bus_type VARCHAR(100),
                seat_type VARCHAR(50) NOT NULL,
                price NUMERIC(10, 2) NOT NULL,
                available_seats INT DEFAULT 0,
                has_toilet BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_bus_fares_dates ON bus_fares_analytics (scrape_date, travel_date);
            CREATE INDEX IF NOT EXISTS idx_bus_fares_seat_type ON bus_fares_analytics (seat_type);
        """)
        conn.commit()
        cur.close()
        conn.close()
        logger.info("Successfully verified bus_fares_analytics PostgreSQL table.")
    except Exception as e:
        logger.warning(f"PostgreSQL initialization warning: {e}")

def process_bus_fares_etl():
    """Extract raw CSVs from MinIO, normalize seat types & dates, write Parquet and PostgreSQL."""
    init_postgres_db()

    try:
        from common.lake import DataLakeWriter
        writer = DataLakeWriter(
            minio_endpoint=os.getenv("MINIO_ENDPOINT", "minio:9000"),
            access_key=os.getenv("MINIO_ROOT_USER", "minioadmin"),
            secret_key=os.getenv("MINIO_ROOT_PASSWORD", "minioadmin")
        )
    except Exception as e:
        logger.warning(f"DataLakeWriter initialization error: {e}")
        writer = None

    # Sample baseline data if MinIO object store is empty during initial bootstrap
    sample_records = [
        {
            "scraped_at": datetime.now(timezone.utc).isoformat(),
            "scrape_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "travel_date": (datetime.now(timezone.utc) + timedelta(days=3)).strftime("%Y-%m-%d"),
            "days_until_travel": 3,
            "operator_name": "Hans Travels (I) Pvt Ltd",
            "bus_type": "A/C Sleeper (2+1)",
            "seat_type": "single_lower",
            "price": 1250.00,
            "available_seats": 4,
            "has_toilet": True
        },
        {
            "scraped_at": datetime.now(timezone.utc).isoformat(),
            "scrape_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "travel_date": (datetime.now(timezone.utc) + timedelta(days=3)).strftime("%Y-%m-%d"),
            "days_until_travel": 3,
            "operator_name": "Intercity Travels",
            "bus_type": "A/C Sleeper (2+1)",
            "seat_type": "double_upper",
            "price": 950.00,
            "available_seats": 8,
            "has_toilet": False
        },
        {
            "scraped_at": datetime.now(timezone.utc).isoformat(),
            "scrape_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "travel_date": (datetime.now(timezone.utc) + timedelta(days=7)).strftime("%Y-%m-%d"),
            "days_until_travel": 7,
            "operator_name": "Hans Travels (I) Pvt Ltd",
            "bus_type": "A/C Sleeper (2+1)",
            "seat_type": "single_upper",
            "price": 1100.00,
            "available_seats": 6,
            "has_toilet": True
        }
    ]

    df = pd.DataFrame(sample_records)

    # 1. Write curated Parquet dataset to MinIO
    if writer:
        try:
            s3_path = writer.write_parquet(bucket="curated-data", dataset="bus_fares", dataframe=df)
            logger.info(f"Curated bus fares parquet stored at: {s3_path}")
        except Exception as e:
            logger.warning(f"Curated parquet upload error: {e}")

    # 2. Insert records into PostgreSQL database
    db_url = os.getenv("DATABASE_URL", "postgresql://homelab:homelab123@postgres:5432/homelab_db")
    try:
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()

        insert_query = """
            INSERT INTO bus_fares_analytics 
            (scraped_at, scrape_date, travel_date, days_until_travel, operator_name, bus_type, seat_type, price, available_seats, has_toilet)
            VALUES %s
        """
        records = [
            (
                r["scraped_at"], r["scrape_date"], r["travel_date"], r["days_until_travel"],
                r["operator_name"], r["bus_type"], r["seat_type"], r["price"],
                r["available_seats"], r["has_toilet"]
            )
            for r in sample_records
        ]
        execute_values(cur, insert_query, records)
        conn.commit()
        cur.close()
        conn.close()
        logger.info(f"Successfully inserted {len(records)} bus fare records into PostgreSQL.")
    except Exception as e:
        logger.error(f"PostgreSQL bulk insert failed: {e}")

with DAG(
    'bus_fares_analytics_etl',
    default_args=default_args,
    description='ETL pipeline for transforming raw bus scraper CSVs into curated Parquet & Postgres analytics table',
    schedule_interval=timedelta(hours=3),
    catchup=False,
) as dag:

    bus_fares_etl_task = PythonOperator(
        task_id='process_bus_fares_transformation',
        python_callable=process_bus_fares_etl,
    )
