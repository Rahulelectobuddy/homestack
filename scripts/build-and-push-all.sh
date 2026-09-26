#!/bin/bash
set -e

REGISTRY=${1:-"localhost:5000"}

echo "🚀 Building & Pushing all Homelab Platform & App images to registry: $REGISTRY..."

echo "📦 [1/6] Airflow..."
docker build -f services/platform/airflow/Dockerfile -t ${REGISTRY}/airflow:latest .
docker push ${REGISTRY}/airflow:latest

echo "📦 [2/6] Backend API..."
docker build -f services/apps/backend/Dockerfile -t ${REGISTRY}/backend:latest .
docker push ${REGISTRY}/backend:latest

echo "📦 [3/6] Frontend App..."
docker build -f services/apps/frontend/Dockerfile -t ${REGISTRY}/frontend:latest services/apps/frontend/
docker push ${REGISTRY}/frontend:latest

echo "📦 [4/6] Bus Scraper..."
docker build -f services/apps/bus-scraper/Dockerfile -t ${REGISTRY}/bus-scraper:latest .
docker push ${REGISTRY}/bus-scraper:latest

echo "📦 [5/6] Health Ingester..."
docker build -f services/apps/health-ingester/Dockerfile -t ${REGISTRY}/health-ingester:latest .
docker push ${REGISTRY}/health-ingester:latest

echo "📦 [6/6] Irrigation MQTT Client..."
docker build -f services/apps/irrigation-mqtt/Dockerfile -t ${REGISTRY}/irrigation-mqtt:latest .
docker push ${REGISTRY}/irrigation-mqtt:latest

echo "✅ All service images built and pushed to $REGISTRY!"
