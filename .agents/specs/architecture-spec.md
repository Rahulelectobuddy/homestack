# Specification: Two-VM Homelab System Architecture

## Target Hardware Specifications
- **Platform VM**: `8GB RAM`, 4 CPU Cores, Local LAN IP `192.168.1.29`.

- **App VM**: `4GB RAM`, 2 CPU Cores, Local LAN IP `192.168.1.11`.

## Service Port Allocation Matrix

| Service Name | VM Target | Internal Container Port | Exposed Host Port | Protocol |
| :--- | :--- | :--- | :--- | :--- |
| Docker Registry | Platform (8GB) | 5000 | 5000 | HTTP |
| Postgres DB | Platform (8GB) | 5432 | 5432 | TCP |
| MinIO API | Platform (8GB) | 9000 | 9000 | HTTP / S3 |
| MinIO Console | Platform (8GB) | 9001 | 9001 | HTTP |
| Mosquitto MQTT | Platform (8GB) | 1883 | 1883 | MQTT TCP |
| Airflow Webserver | Platform (8GB) | 8080 | 8080 | HTTP |
| Prometheus | Platform (8GB) | 9090 | 9090 | HTTP |
| Loki | Platform (8GB) | 3100 | 3100 | HTTP |
| Grafana | Platform (8GB) | 3000 | 3001 | HTTP |
| Backend API | App (4GB) | 8000 | 8000 | HTTP |
| Frontend App | App (4GB) | 3000 | 3000 | HTTP |
| Keycloak IAM | App (4GB) | 8080 | 8080 | HTTP |
| Health Ingester | App (4GB) | 8001 | 8001 | HTTP |
