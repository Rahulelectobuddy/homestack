# Specification: Unified Homelab System Architecture

## Target Hardware Specifications
- **Single Homelab Host**: `192.168.1.29`

## Unified Service Port Allocation Matrix

| Service Name | Container Target | Internal Port | Exposed Host Port | Protocol |
| :--- | :--- | :--- | :--- | :--- |
| Docker Registry | `local_registry` | 5000 | 5000 | HTTP |
| Postgres DB | `postgres` | 5432 | 5432 | TCP |
| MinIO API | `minio` | 9000 | 9000 | HTTP / S3 |
| MinIO Console | `minio` | 9001 | 9001 | HTTP |
| Mosquitto MQTT | `mqtt_broker` | 1883 | 1883 | MQTT TCP |
| Airflow Webserver | `airflow_webserver` | 8080 | 8080 | HTTP |
| Keycloak IAM | `app_keycloak` | 8080 | 8085 | HTTP |
| Backend API | `app_backend` | 8000 | 8000 | HTTP |
| Frontend App | `app_frontend` | 3000 | 3000 | HTTP |
| Health Ingester | `app_health_ingester` | 8001 | 8001 | HTTP |
| Prometheus | `prometheus` | 9090 | 9090 | HTTP |
| Loki | `loki` | 3100 | 3100 | HTTP |
| Grafana | `grafana` | 3000 | 3001 | HTTP |
