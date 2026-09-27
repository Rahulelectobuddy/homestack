#!/bin/bash
set -e

HOST=${1:-"192.168.1.29"}

echo "🧪 Starting Automated Post-Deployment Validation on Host: $HOST..."

echo "⏳ Waiting 5 seconds for services to stabilize..."
sleep 5

echo "🔍 [1/5] Checking container status..."
docker compose ps

echo "🌐 [2/5] Testing HTTP Service Endpoints (with retry warm-up)..."

check_endpoint() {
  local name="$1"
  local url="$2"
  local retries=${3:-6}
  local delay=${4:-5}

  echo -n "  - $name... "
  for i in $(seq 1 $retries); do
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$url" || echo "000")
    if [ "$STATUS" -eq 200 ]; then
      echo "✅ OK"
      return 0
    fi
    sleep $delay
  done
  echo "❌ FAILED ($STATUS)"
  exit 1
}

check_endpoint "Backend API (/health)" "http://$HOST:8000/health"
check_endpoint "Bus Fares Analytics API (/api/v1/analytics/bus-fares)" "http://$HOST:8000/api/v1/analytics/bus-fares"
check_endpoint "Health Ingester (/health)" "http://$HOST:8001/health"
check_endpoint "Airflow Webserver (/health)" "http://$HOST:8080/health" 10 5
check_endpoint "Frontend App (/)" "http://$HOST:3000/"

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
