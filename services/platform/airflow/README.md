# Airflow Pipeline Orchestration

## Purpose
Orchestrates scheduled batch ingestion, data transformations (raw -> staging -> curated analytical tables in Parquet format), and model maintenance.

## Directory Structure
- `dags/`: Python DAG definitions.
- `Dockerfile`: Custom Airflow container image with data lake providers installed.
- `requirements.txt`: Python packages available inside Airflow workers.

## Deployment Target
Deploys to **8GB Platform VM**.
