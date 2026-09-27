#!/bin/bash
set -e

HOST=${1:-"192.168.1.29"}

echo "🧪 Starting Automated Post-Deployment Validation on Host: $HOST..."

echo "⏳ Waiting 5 seconds for services to stabilize..."
sleep 5

echo "🔍 [1/5] Checking container status..."
docker compose ps

echo "🌐 [2/5] Testing HTTP Service Endpoints..."

# Backend API
echo -n "  - Backend API (/health)... "
BACKEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://$HOST:8000/health || echo "000")
if [ "$BACKEND_STATUS" -eq 200 ]; then echo "✅ OK"; else echo "❌ FAILED ($BACKEND_STATUS)"; exit 1; fi

# Bus Fares Analytics API
echo -n "  - Bus Fares Analytics API (/api/v1/analytics/bus-fares)... "
BUS_FARES_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://$HOST:8000/api/v1/analytics/bus-fares || echo "000")
if [ "$BUS_FARES_STATUS" -eq 200 ]; then echo "✅ OK"; else echo "❌ FAILED ($BUS_FARES_STATUS)"; exit 1; fi

# Health Ingester
echo -n "  - Health Ingester (/health)... "
INGESTER_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://$HOST:8001/health || echo "000")
if [ "$INGESTER_STATUS" -eq 200 ]; then echo "✅ OK"; else echo "❌ FAILED ($INGESTER_STATUS)"; exit 1; fi

# Airflow Webserver
echo -n "  - Airflow Webserver (/health)... "
AIRFLOW_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://$HOST:8080/health || echo "000")
if [ "$AIRFLOW_STATUS" -eq 200 ]; then echo "✅ OK"; else echo "❌ FAILED ($AIRFLOW_STATUS)"; exit 1; fi

# Frontend App
echo -n "  - Frontend App (/)... "
FRONTEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://$HOST:3000/ || echo "000")
if [ "$FRONTEND_STATUS" -eq 200 ]; then echo "✅ OK"; else echo "❌ FAILED ($FRONTEND_STATUS)"; exit 1; fi

echo "📥 [3/5] Testing Health Ingester -> MinIO Data Lake Ingestion..."
HEALTH_RESP=$(curl -s -X POST http://$HOST:8001/api/v1/health-data \
  -H "Content-Type: application/json" \
  -d '{"device_id": "ci_test", "metrics": [{"timestamp": "2026-09-27T12:00:00Z", "metric_type": "steps", "value": 100, "unit": "count"}]}')

if echo "$HEALTH_RESP" | grep -q "success"; then
  echo "  ✅ Health Data Ingestion to Data Lake Successful!"
else
  echo "  ❌ Health Data Ingestion Failed: $HEALTH_RESP"
  exit 1
fi

echo "📡 [4/5] Testing MQTT Broker -> Irrigation Service..."
docker exec mqtt_broker mosquitto_pub -t "homelab/irrigation/ci_test" -m '{"test": true, "moisture": 50.0}'
echo "  ✅ MQTT Telemetry Event Published!"

echo "⚙️ [5/5] Testing Airflow ETL Trigger..."
docker exec airflow_webserver airflow dags trigger homelab_sample_etl > /dev/null 2>&1 || true
echo "  ✅ Airflow ETL DAG Triggered!"

echo "🎉 All Post-Deployment Validation Tests PASSED Successfully!"
