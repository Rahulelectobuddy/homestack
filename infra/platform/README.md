# Platform VM Infrastructure (`8GB RAM`)

## Services Hosted
- Local Docker Registry (`:5000`)
- Shared Postgres Database (`:5432`)
- MinIO Data Lake (`:9000`, Console `:9001`)
- Mosquitto MQTT Broker (`:1883`)
- Apache Airflow Orchestration (`:8080`)
- Monitoring Stack (Prometheus `:9090`, Loki `:3100`, Grafana `:3001`)
- GitHub Actions Self-Hosted Build Runner

## Managing Services
```bash
# Start all platform services
docker compose pull && docker compose up -d

# Stop platform services
docker compose down
```
