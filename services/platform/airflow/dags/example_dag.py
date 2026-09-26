from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator

default_args = {
    'owner': 'homelab',
    'depends_on_past': False,
    'start_date': datetime(2026, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

def sample_etl_task():
    print("Executing sample homelab ETL pipeline: processing raw bucket files to analytical parquet tables.")
    try:
        import pandas as pd
        from common.lake import DataLakeWriter

        writer = DataLakeWriter(
            minio_endpoint="minio:9000",
            access_key="minioadmin",
            secret_key="minioadmin"
        )
        # Transform raw bus scraper / health / irrigation data into curated parquet tables
        curated_df = pd.DataFrame([
            {"route": "pune-to-indore", "avg_price": 1250.0, "processed_at": datetime.now().isoformat()},
        ])
        s3_url = writer.write_parquet(bucket="curated-data", dataset="bus_fares", dataframe=curated_df)
        print(f"✅ ETL complete! Curated parquet written to: {s3_url}")
    except Exception as e:
        print(f"⚠️ ETL Task execution warning: {e}")

with DAG(
    'homelab_sample_etl',
    default_args=default_args,
    description='Sample ETL DAG for Homelab Data Lake',
    schedule_interval=timedelta(days=1),
    catchup=False,
) as dag:

    etl_task = PythonOperator(
        task_id='process_raw_to_curated',
        python_callable=sample_etl_task,
    )

