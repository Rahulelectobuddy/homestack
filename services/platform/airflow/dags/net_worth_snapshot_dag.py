import requests
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator

default_args = {
    'owner': 'homelab',
    'depends_on_past': False,
    'start_date': datetime(2026, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

def trigger_net_worth_weekly_snapshot():
    """
    Triggers backend net worth snapshot REST API to capture weekly Net Worth,
    Asset Valuations, Liabilities, and FX rates into PostgreSQL and Data Lake.
    """
    backend_url = "http://backend:8000/api/v1/net-worth/snapshots"
    fallback_url = "http://localhost:8000/api/v1/net-worth/snapshots"

    print(f"Executing weekly net worth snapshot pipeline trigger at: {datetime.now().isoformat()}")
    
    response = None
    try:
        response = requests.post(backend_url, timeout=15)
    except Exception as e:
        print(f"Backend container DNS connection note: {e}. Trying fallback URL: {fallback_url}")
        try:
            response = requests.post(fallback_url, timeout=15)
        except Exception as e2:
            print(f"⚠️ Primary and fallback snapshot triggers unreachable: {e2}")

    if response and response.status_code == 200:
        data = response.json()
        print(f"✅ Net worth weekly snapshot successfully recorded: {data}")
    else:
        status = response.status_code if response else "No response"
        print(f"⚠️ Weekly snapshot trigger returned status code: {status}")

with DAG(
    'net_worth_weekly_snapshot_pipeline',
    default_args=default_args,
    description='Weekly Automated Snapshot & Trend Archive Pipeline for Net Worth Engine',
    schedule_interval='0 0 * * 0',  # Weekly on Sunday midnight
    catchup=False,
) as dag:

    snapshot_task = PythonOperator(
        task_id='capture_weekly_net_worth_snapshot',
        python_callable=trigger_net_worth_weekly_snapshot,
    )
