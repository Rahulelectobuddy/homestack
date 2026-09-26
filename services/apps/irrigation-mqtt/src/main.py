import os
import time
from typing import Any
from common.mqtt import SharedMQTTClient

from common.lake import DataLakeWriter
from common.logging import setup_logging

logger = setup_logging(service_name="irrigation-mqtt", level="INFO")

MQTT_BROKER = os.getenv("MQTT_BROKER_HOST", "mqtt-broker")
MQTT_PORT = int(os.getenv("MQTT_BROKER_PORT", "1883"))
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "")
TOPIC = "homelab/irrigation/#"

writer = None
if MINIO_ENDPOINT:
    try:
        writer = DataLakeWriter(
            minio_endpoint=MINIO_ENDPOINT,
            access_key=os.getenv("MINIO_ROOT_USER", "minioadmin"),
            secret_key=os.getenv("MINIO_ROOT_PASSWORD", "minioadmin")
        )
    except Exception as e:
        logger.warning(f"Could not initialize DataLakeWriter: {e}")


def on_irrigation_message(topic: str, payload: Any):
    logger.info(f"Received message on {topic}: {payload}")
    if writer:
        try:
            event_data = payload if isinstance(payload, dict) else {"topic": topic, "payload": payload}
            s3_url = writer.write_json(
                bucket="raw-data",
                dataset="irrigation",
                data=event_data
            )
            logger.info(f"Written irrigation event to Data Lake: {s3_url}")
        except Exception as e:
            logger.error(f"Error persisting irrigation message to Data Lake: {e}")


def main():
    logger.info("Starting Balcony Irrigation MQTT Client...")
    client = SharedMQTTClient(broker=MQTT_BROKER, port=MQTT_PORT, client_id="irrigation-service")
    client.subscribe(TOPIC, on_irrigation_message)
    client.connect()

    while True:
        time.sleep(1)


if __name__ == "__main__":
    main()

