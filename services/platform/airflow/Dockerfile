FROM apache/airflow:2.8.1-python3.11

USER root
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

USER airflow

COPY libs/common-python /libs/common-python
RUN pip install --no-cache-dir /libs/common-python

COPY services/platform/airflow/requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt

COPY services/platform/airflow/dags/ ${AIRFLOW_HOME}/dags/

