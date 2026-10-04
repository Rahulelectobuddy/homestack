import os
import json
import time
import threading
import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Optional

import psycopg2
from psycopg2.extras import RealDictCursor

from common.mqtt import SharedMQTTClient
from common.lake import DataLakeWriter
from common.logging import setup_logging

logger = setup_logging(service_name="irrigation-mqtt", level="INFO")

MQTT_BROKER = os.getenv("MQTT_BROKER_HOST", "mqtt-broker")
MQTT_PORT = int(os.getenv("MQTT_BROKER_PORT", "1883"))
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://homelab:homelab123@postgres:5432/homelab_db")

DEFAULT_DEVICE_ID = "esp32-balcony-03"
AUTO_STOP_INTERVAL_SECONDS = 60  # Mandatory 1-minute auto-stop safety interval

# Standard ESP32 MQTT Topics
MQTT_TOPIC_RELAY1 = os.getenv("MQTT_TOPIC_RELAY1", "esp32/balcony/relay1")
MQTT_TOPIC_CMD = os.getenv("MQTT_TOPIC_CMD", "esp32/balcony/cmd")
MQTT_TOPICS_SUB = ["esp32/balcony/#", "esp32/03/#", "homelab/irrigation/#"]

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


def get_db_connection():
    return psycopg2.connect(DATABASE_URL)


def process_telemetry_message(topic: str, payload: Any):
    """Processes heartbeat (HBT), online status, and relay state from ESP32."""
    now = datetime.now(timezone.utc)
    
    if not isinstance(payload, dict):
        try:
            payload = json.loads(payload)
        except Exception:
            payload = {"raw": str(payload)}

    device_id = payload.get("device_id", DEFAULT_DEVICE_ID)
    status_str = payload.get("status", "online")
    relay1_state = payload.get("relay1") or payload.get("relay1_state") or payload.get("relay") or payload.get("state")
    rssi = payload.get("rssi") or payload.get("wifi_rssi")

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        update_fields = ["hbt = %s", "updated_at = %s"]
        params = [now, now]

        if status_str and status_str != "watering":
            update_fields.append("status = %s")
            params.append(status_str)

        if relay1_state:
            state_val = str(relay1_state).upper()
            if state_val in ["ON", "1", "TRUE"]:
                update_fields.append("relay1_state = 'ON'")
            elif state_val in ["OFF", "0", "FALSE"]:
                update_fields.append("relay1_state = 'OFF'")

        if rssi is not None:
            update_fields.append("rssi = %s")
            params.append(int(rssi))

        params.append(device_id)

        sql = f"""
            UPDATE irrigation_devices
            SET {', '.join(update_fields)}
            WHERE device_id = %s;
        """
        cur.execute(sql, params)

        event_type = "hbt" if ("hbt" in topic or "status" in topic) else "telemetry"
        cur.execute("""
            INSERT INTO irrigation_logs (device_id, event_type, topic, details)
            VALUES (%s, %s, %s, %s);
        """, (device_id, event_type, topic, json.dumps(payload)))

        conn.commit()
        cur.close()
        conn.close()
        logger.info(f"[MQTT Processor] Updated ESP32 device status & HBT for {device_id} on {topic}")

    except Exception as e:
        logger.error(f"[MQTT Processor] DB error updating telemetry/HBT: {e}")


def on_irrigation_message(topic: str, payload: Any):
    logger.info(f"Received message on {topic}: {payload}")
    
    if "cmd" not in topic and "relay1" not in topic:
        process_telemetry_message(topic, payload)

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


def schedule_runner_loop():
    """Background loop checking active schedules and executing 1-min watering tasks."""
    mqtt_client = SharedMQTTClient(broker=MQTT_BROKER, port=MQTT_PORT, client_id="irrigation-scheduler")
    
    while True:
        try:
            now = datetime.now(timezone.utc)
            current_time = now.strftime("%H:%M")
            current_day = now.strftime("%a")

            conn = get_db_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute("SELECT * FROM irrigation_schedules WHERE is_active = TRUE;")
            schedules = cur.fetchall()

            for sched in schedules:
                sched_time = sched["time_of_day"]
                sched_days = [d.strip() for d in sched["days_of_week"].split(",")]

                if current_time == sched_time and (current_day in sched_days or "All" in sched_days or len(sched_days) == 7):
                    last_run = sched.get("last_run")
                    already_ran_today = False
                    if last_run:
                        if last_run.tzinfo is None:
                            last_run = last_run.replace(tzinfo=timezone.utc)
                        if (now - last_run).total_seconds() < 120:
                            already_ran_today = True

                    if not already_ran_today:
                        logger.info(f"[Scheduler] Triggering scheduled watering: {sched['name']} ({sched_time})")
                        duration = AUTO_STOP_INTERVAL_SECONDS
                        auto_stop_at = now + timedelta(seconds=duration)

                        cur.execute("""
                            UPDATE irrigation_devices
                            SET relay1_state = 'ON',
                                status = 'watering',
                                watering_started_at = %s,
                                watering_auto_stop_at = %s,
                                updated_at = CURRENT_TIMESTAMP
                            WHERE device_id = %s;
                        """, (now, auto_stop_at, DEFAULT_DEVICE_ID))

                        cur.execute("""
                            UPDATE irrigation_schedules
                            SET last_run = %s
                            WHERE id = %s;
                        """, (now, sched["id"]))

                        log_details = {
                            "schedule_id": sched["id"],
                            "schedule_name": sched["name"],
                            "duration_seconds": duration,
                            "auto_stop_interval": "1 min"
                        }
                        cur.execute("""
                            INSERT INTO irrigation_logs (device_id, event_type, topic, details, duration_seconds)
                            VALUES (%s, %s, %s, %s, %s);
                        """, (DEFAULT_DEVICE_ID, "scheduled_trigger", MQTT_TOPIC_RELAY1, json.dumps(log_details), duration))

                        conn.commit()

                        cmd_payload = {
                            "command": "WATER_ON",
                            "relay": 1,
                            "state": "ON",
                            "duration_seconds": duration,
                            "auto_stop_interval": "1 min",
                            "source": "schedule",
                            "schedule_id": sched["id"],
                            "timestamp": now.isoformat()
                        }
                        mqtt_client.publish(MQTT_TOPIC_RELAY1, cmd_payload)
                        mqtt_client.publish(MQTT_TOPIC_CMD, cmd_payload)
                        mqtt_client.publish("homelab/irrigation/cmd", cmd_payload)

            cur.close()
            conn.close()

        except Exception as e:
            logger.error(f"[Scheduler Loop] Error during schedule check: {e}")

        time.sleep(15)


def auto_stop_safety_loop():
    """Background safety guard loop ensuring watering automatically turns off after 1 minute (60s)."""
    mqtt_client = SharedMQTTClient(broker=MQTT_BROKER, port=MQTT_PORT, client_id="irrigation-safety-guard")

    while True:
        try:
            now = datetime.now(timezone.utc)
            conn = get_db_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)

            cur.execute("""
                SELECT device_id, watering_auto_stop_at
                FROM irrigation_devices
                WHERE relay1_state = 'ON' AND watering_auto_stop_at IS NOT NULL;
            """)
            active_devices = cur.fetchall()

            for dev in active_devices:
                auto_stop_at = dev["watering_auto_stop_at"]
                if auto_stop_at.tzinfo is None:
                    auto_stop_at = auto_stop_at.replace(tzinfo=timezone.utc)

                if now >= auto_stop_at:
                    device_id = dev["device_id"]
                    logger.info(f"[Safety Guard] 1-minute auto-cutoff interval reached for {device_id}. Stopping Relay 1.")

                    cur.execute("""
                        UPDATE irrigation_devices
                        SET relay1_state = 'OFF',
                            status = 'online',
                            watering_started_at = NULL,
                            watering_auto_stop_at = NULL,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE device_id = %s;
                    """, (device_id,))

                    log_details = {
                        "action": "auto_stop_1min_timeout",
                        "cutoff_at": now.isoformat(),
                        "note": "Watering automatically stopped after 1 minute interval."
                    }
                    cur.execute("""
                        INSERT INTO irrigation_logs (device_id, event_type, topic, details, duration_seconds)
                        VALUES (%s, %s, %s, %s, %s);
                    """, (device_id, "auto_stop", MQTT_TOPIC_RELAY1, json.dumps(log_details), 0))

                    conn.commit()

                    cmd_payload = {
                        "command": "WATER_OFF",
                        "relay": 1,
                        "state": "OFF",
                        "reason": "auto_stop_1min_timeout",
                        "timestamp": now.isoformat()
                    }
                    mqtt_client.publish(MQTT_TOPIC_RELAY1, cmd_payload)
                    mqtt_client.publish(MQTT_TOPIC_CMD, cmd_payload)
                    mqtt_client.publish("homelab/irrigation/cmd", cmd_payload)

            cur.close()
            conn.close()

        except Exception as e:
            logger.error(f"[Safety Guard Loop] Error during auto-stop check: {e}")

        time.sleep(5)


def main():
    logger.info("Starting Balcony Irrigation MQTT Client & Safety Scheduler Service...")
    
    client = SharedMQTTClient(broker=MQTT_BROKER, port=MQTT_PORT, client_id="irrigation-mqtt-service")
    for topic_pat in MQTT_TOPICS_SUB:
        client.subscribe(topic_pat, on_irrigation_message)
    client.connect()

    scheduler_thread = threading.Thread(target=schedule_runner_loop, daemon=True)
    scheduler_thread.start()

    safety_thread = threading.Thread(target=auto_stop_safety_loop, daemon=True)
    safety_thread.start()

    logger.info(f"[Main] Subscribed to {MQTT_TOPICS_SUB}. All safety loops operational.")

    while True:
        time.sleep(1)


if __name__ == "__main__":
    main()
