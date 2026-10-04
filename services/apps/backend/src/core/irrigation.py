import os
import json
import time
import logging
import threading
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional

import psycopg2
from psycopg2.extras import RealDictCursor
from pydantic import BaseModel, Field

from common.mqtt import SharedMQTTClient
from common.lake import DataLakeWriter

logger = logging.getLogger(__name__)

# --- Configuration Constants ---
MQTT_BROKER = os.getenv("MQTT_BROKER_HOST", "mqtt-broker")
MQTT_PORT = int(os.getenv("MQTT_BROKER_PORT", "1883"))
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://homelab:homelab123@postgres:5432/homelab_db")
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "")

DEFAULT_DEVICE_ID = "esp32-balcony-03"
AUTO_STOP_INTERVAL_SECONDS = 60  # Mandatory 1-minute auto-stop safety interval

# Standard ESP32 MQTT Topics
MQTT_TOPIC_RELAY1 = os.getenv("MQTT_TOPIC_RELAY1", "esp32/balcony/relay1")
MQTT_TOPIC_CMD = os.getenv("MQTT_TOPIC_CMD", "esp32/balcony/cmd")
MQTT_TOPIC_STATUS = os.getenv("MQTT_TOPIC_STATUS", "esp32/balcony/status")


# --- Pydantic DTO Schemas ---

class DeviceStatusOut(BaseModel):
    device_id: str
    device_name: str
    status: str  # 'online', 'offline', 'watering'
    hbt: Optional[str] = None
    hbt_timestamp: Optional[float] = None
    last_seen_seconds_ago: int
    is_online: bool
    relay1_state: str  # 'ON' or 'OFF'
    rssi: int
    watering_active: bool
    watering_started_at: Optional[str] = None
    watering_auto_stop_at: Optional[str] = None
    remaining_watering_seconds: int = 0
    auto_stop_interval_seconds: int = AUTO_STOP_INTERVAL_SECONDS
    mqtt_command_topic: str = MQTT_TOPIC_RELAY1
    note: str = "Watering automatically stops after 1 minute (60s) interval."


class TriggerWaterRequest(BaseModel):
    relay: int = Field(default=1, description="Relay index to trigger (1 for Balcony Irrigation)")
    duration_seconds: int = Field(default=60, description="Watering duration in seconds (default: 60s / 1 min)")


class ScheduleCreate(BaseModel):
    name: str = Field(..., example="Daily Morning Balcony Water")
    time_of_day: str = Field(..., example="08:00", description="Time of day in HH:MM 24h format")
    days_of_week: List[str] = Field(default=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"])
    duration_seconds: int = Field(default=60, description="Duration in seconds (default: 60s / 1 min)")
    is_active: bool = Field(default=True)


class ScheduleOut(BaseModel):
    id: int
    name: str
    time_of_day: str
    days_of_week: List[str]
    duration_seconds: int
    relay: int
    is_active: bool
    last_run: Optional[str] = None
    created_at: str


class WateringHistoryOut(BaseModel):
    id: int
    device_id: str
    event_type: str
    source: str
    relay: int
    duration_seconds: int
    status: str
    triggered_at: str
    stopped_at: Optional[str] = None
    details: Dict[str, Any]


class IrrigationLogOut(BaseModel):
    id: int
    device_id: str
    event_type: str
    topic: Optional[str] = None
    details: Dict[str, Any]
    duration_seconds: Optional[int] = 60
    created_at: Optional[str] = None


# --- Database Connection Helper ---

def get_db_connection():
    return psycopg2.connect(DATABASE_URL)


# --- Database Initialization ---

def init_irrigation_db_tables():
    """Initializes PostgreSQL tables for Balcony Irrigation ESP32 system."""
    for attempt in range(1, 10):
        try:
            conn = get_db_connection()
            cur = conn.cursor()

            # 1. Devices & Heartbeat Status Table (Moisture & Temp removed)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS irrigation_devices (
                    device_id VARCHAR(64) PRIMARY KEY,
                    device_name VARCHAR(128) NOT NULL,
                    status VARCHAR(32) NOT NULL DEFAULT 'offline',
                    hbt TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    relay1_state VARCHAR(10) NOT NULL DEFAULT 'OFF',
                    rssi INTEGER DEFAULT -65,
                    watering_started_at TIMESTAMP WITH TIME ZONE,
                    watering_auto_stop_at TIMESTAMP WITH TIME ZONE,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # Seed default ESP32 device if not exists
            cur.execute("""
                INSERT INTO irrigation_devices (device_id, device_name, status, hbt, relay1_state, rssi)
                VALUES (%s, %s, %s, CURRENT_TIMESTAMP, %s, %s)
                ON CONFLICT (device_id) DO NOTHING;
            """, (DEFAULT_DEVICE_ID, "Balcony Irrigation ESP32 (Project 03)", "online", "OFF", -62))

            # 2. Automated Watering Schedules Table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS irrigation_schedules (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(128) NOT NULL,
                    time_of_day VARCHAR(5) NOT NULL,
                    days_of_week TEXT NOT NULL DEFAULT 'Mon,Tue,Wed,Thu,Fri,Sat,Sun',
                    duration_seconds INTEGER DEFAULT 60,
                    relay INTEGER DEFAULT 1,
                    is_active BOOLEAN DEFAULT TRUE,
                    last_run TIMESTAMP WITH TIME ZONE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # Seed initial default schedule if table is empty
            cur.execute("SELECT COUNT(*) FROM irrigation_schedules;")
            if cur.fetchone()[0] == 0:
                cur.execute("""
                    INSERT INTO irrigation_schedules (name, time_of_day, days_of_week, duration_seconds, relay, is_active)
                    VALUES (%s, %s, %s, %s, %s, %s);
                """, ("Morning Balcony Shower", "07:30", "Mon,Tue,Wed,Thu,Fri,Sat,Sun", 60, 1, True))

            # 3. Telemetry, Heartbeat & Watering History Logs Table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS irrigation_logs (
                    id SERIAL PRIMARY KEY,
                    device_id VARCHAR(64) DEFAULT 'esp32-balcony-03',
                    event_type VARCHAR(64) NOT NULL,
                    topic VARCHAR(256),
                    details JSONB DEFAULT '{}'::jsonb,
                    duration_seconds INTEGER DEFAULT 60,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
            """)

            conn.commit()
            cur.close()
            conn.close()
            logger.info("[Irrigation DB] Initialization complete.")
            return
        except Exception as e:
            logger.warning(f"[Irrigation DB] Postgres database not ready yet (attempt {attempt}/10): {e}")
            time.sleep(2)


# --- Helper to Publish MQTT Message ---

def publish_mqtt_command(topic: str, payload: Any) -> bool:
    """Publishes command payload (JSON or string) to MQTT Broker."""
    try:
        client = SharedMQTTClient(broker=MQTT_BROKER, port=MQTT_PORT, client_id="backend-irrigation-pub")
        if isinstance(payload, dict):
            client.publish(topic, payload)
        else:
            # Send raw string (e.g. "ON" / "OFF")
            raw_payload = {"state": str(payload)}
            client.publish(topic, raw_payload)
        logger.info(f"[Irrigation MQTT] Published to {topic}: {payload}")
        return True
    except Exception as e:
        logger.error(f"[Irrigation MQTT] Failed to publish to {topic}: {e}")
        return False


# --- Core Irrigation Business Logic ---

def get_device_status(device_id: str = DEFAULT_DEVICE_ID) -> Dict[str, Any]:
    """Retrieves real-time status and heartbeat metric for ESP32 balcony watering device."""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM irrigation_devices WHERE device_id = %s;", (device_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()

    now = datetime.now(timezone.utc)

    if not row:
        return {
            "device_id": device_id,
            "device_name": "Balcony Irrigation ESP32 (Project 03)",
            "status": "offline",
            "hbt": now.isoformat(),
            "hbt_timestamp": now.timestamp(),
            "last_seen_seconds_ago": 999,
            "is_online": False,
            "relay1_state": "OFF",
            "rssi": -65,
            "watering_active": False,
            "watering_started_at": None,
            "watering_auto_stop_at": None,
            "remaining_watering_seconds": 0,
            "auto_stop_interval_seconds": AUTO_STOP_INTERVAL_SECONDS,
            "mqtt_command_topic": MQTT_TOPIC_RELAY1,
            "note": "Watering automatically stops after 1 minute (60s) interval."
        }

    hbt_dt = row["hbt"]
    if hbt_dt is None:
        hbt_dt = now
    elif hbt_dt.tzinfo is None:
        hbt_dt = hbt_dt.replace(tzinfo=timezone.utc)

    last_seen_seconds_ago = int((now - hbt_dt).total_seconds())
    is_online = last_seen_seconds_ago < 120

    relay1_state = row.get("relay1_state", "OFF")
    watering_auto_stop_at = row.get("watering_auto_stop_at")

    watering_active = False
    remaining_watering_seconds = 0

    if relay1_state == "ON" and watering_auto_stop_at:
        if watering_auto_stop_at.tzinfo is None:
            watering_auto_stop_at = watering_auto_stop_at.replace(tzinfo=timezone.utc)
        diff = int((watering_auto_stop_at - now).total_seconds())
        if diff > 0:
            watering_active = True
            remaining_watering_seconds = diff
        else:
            stop_water_relay1(device_id=device_id, reason="auto_stop_1min_timeout")
            relay1_state = "OFF"

    status_str = "watering" if watering_active else ("online" if is_online else "offline")

    return {
        "device_id": row["device_id"],
        "device_name": row["device_name"],
        "status": status_str,
        "hbt": hbt_dt.isoformat(),
        "hbt_timestamp": hbt_dt.timestamp(),
        "last_seen_seconds_ago": last_seen_seconds_ago,
        "is_online": is_online,
        "relay1_state": relay1_state,
        "rssi": int(row.get("rssi") or -65),
        "watering_active": watering_active,
        "watering_started_at": row.get("watering_started_at").isoformat() if row.get("watering_started_at") else None,
        "watering_auto_stop_at": row.get("watering_auto_stop_at").isoformat() if row.get("watering_auto_stop_at") else None,
        "remaining_watering_seconds": remaining_watering_seconds,
        "auto_stop_interval_seconds": AUTO_STOP_INTERVAL_SECONDS,
        "mqtt_command_topic": MQTT_TOPIC_RELAY1,
        "note": "Watering automatically stops after 1 minute (60s) interval."
    }


def trigger_water_relay1(
    device_id: str = DEFAULT_DEVICE_ID,
    duration_seconds: int = 60,
    source: str = "manual",
    schedule_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Triggers Relay 1 for Balcony Irrigation.
    Mandatory Rule: Watering automatically stops after a 1-minute (60s) interval.
    Publishes to esp32/balcony/relay1, esp32/balcony/cmd, and homelab/irrigation/cmd.
    """
    duration_seconds = AUTO_STOP_INTERVAL_SECONDS
    now = datetime.now(timezone.utc)
    auto_stop_at = now + timedelta(seconds=duration_seconds)

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE irrigation_devices
        SET relay1_state = 'ON',
            status = 'watering',
            watering_started_at = %s,
            watering_auto_stop_at = %s,
            updated_at = CURRENT_TIMESTAMP
        WHERE device_id = %s;
    """, (now, auto_stop_at, device_id))

    log_details = {
        "action": "trigger_relay1",
        "duration_seconds": duration_seconds,
        "auto_stop_interval": "1 min",
        "source": source,
        "schedule_id": schedule_id,
        "auto_stop_scheduled_for": auto_stop_at.isoformat()
    }

    cur.execute("""
        INSERT INTO irrigation_logs (device_id, event_type, topic, details, duration_seconds)
        VALUES (%s, %s, %s, %s, %s);
    """, (device_id, f"{source}_trigger", MQTT_TOPIC_RELAY1, json.dumps(log_details), duration_seconds))

    conn.commit()
    cur.close()
    conn.close()

    # Publish MQTT commands to all standard topic patterns
    json_cmd = {
        "command": "WATER_ON",
        "relay": 1,
        "state": "ON",
        "duration_seconds": duration_seconds,
        "auto_stop_interval": "1 min",
        "source": source,
        "schedule_id": schedule_id,
        "timestamp": now.isoformat()
    }
    
    publish_mqtt_command(MQTT_TOPIC_RELAY1, json_cmd)
    publish_mqtt_command(MQTT_TOPIC_CMD, json_cmd)
    publish_mqtt_command("homelab/irrigation/cmd", json_cmd)
    publish_mqtt_command("esp32/03/relay1", {"state": "ON", "duration": duration_seconds})

    def _auto_stop_timer():
        time.sleep(duration_seconds)
        stop_water_relay1(device_id=device_id, reason="auto_stop_1min_timeout")

    timer_thread = threading.Thread(target=_auto_stop_timer, daemon=True)
    timer_thread.start()

    logger.info(f"[Irrigation] Relay 1 triggered for {duration_seconds}s on {MQTT_TOPIC_RELAY1}.")

    return {
        "success": True,
        "message": f"Watering initiated for Relay 1. Auto-cutoff scheduled in 1 minute (60 seconds).",
        "device_id": device_id,
        "relay": 1,
        "duration_seconds": duration_seconds,
        "watering_started_at": now.isoformat(),
        "watering_auto_stop_at": auto_stop_at.isoformat(),
        "mqtt_topics_notified": [MQTT_TOPIC_RELAY1, MQTT_TOPIC_CMD, "homelab/irrigation/cmd"],
        "auto_stop_note": "Watering automatically stops after 1 minute (60s) interval."
    }


def stop_water_relay1(device_id: str = DEFAULT_DEVICE_ID, reason: str = "manual_stop") -> Dict[str, Any]:
    """Stops Relay 1 watering immediately and updates device state."""
    now = datetime.now(timezone.utc)

    conn = get_db_connection()
    cur = conn.cursor()

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
        "action": "stop_relay1",
        "reason": reason,
        "stopped_at": now.isoformat()
    }

    cur.execute("""
        INSERT INTO irrigation_logs (device_id, event_type, topic, details, duration_seconds)
        VALUES (%s, %s, %s, %s, %s);
    """, (device_id, "auto_stop" if "auto_stop" in reason else "manual_stop", MQTT_TOPIC_RELAY1, json.dumps(log_details), 0))

    conn.commit()
    cur.close()
    conn.close()

    json_cmd = {
        "command": "WATER_OFF",
        "relay": 1,
        "state": "OFF",
        "reason": reason,
        "timestamp": now.isoformat()
    }
    publish_mqtt_command(MQTT_TOPIC_RELAY1, json_cmd)
    publish_mqtt_command(MQTT_TOPIC_CMD, json_cmd)
    publish_mqtt_command("homelab/irrigation/cmd", json_cmd)
    publish_mqtt_command("esp32/03/relay1", {"state": "OFF", "reason": reason})

    logger.info(f"[Irrigation] Relay 1 stopped ({reason}).")

    return {
        "success": True,
        "message": f"Relay 1 stopped ({reason}).",
        "device_id": device_id,
        "relay": 1,
        "status": "OFF"
    }


# --- Schedule Functions ---

def get_schedules() -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM irrigation_schedules ORDER BY id ASC;")
    rows = cur.fetchall()
    cur.close()
    conn.close()

    schedules = []
    for r in rows:
        days_str = r.get("days_of_week", "Mon,Tue,Wed,Thu,Fri,Sat,Sun")
        days_list = [d.strip() for d in days_str.split(",") if d.strip()]
        schedules.append({
            "id": r["id"],
            "name": r["name"],
            "time_of_day": r["time_of_day"],
            "days_of_week": days_list,
            "duration_seconds": r.get("duration_seconds") or AUTO_STOP_INTERVAL_SECONDS,
            "relay": r.get("relay") or 1,
            "is_active": bool(r.get("is_active")),
            "last_run": r["last_run"].isoformat() if r.get("last_run") else None,
            "created_at": r["created_at"].isoformat() if r.get("created_at") else None
        })
    return schedules


def create_schedule(schedule: ScheduleCreate) -> Dict[str, Any]:
    days_str = ",".join(schedule.days_of_week)
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        INSERT INTO irrigation_schedules (name, time_of_day, days_of_week, duration_seconds, relay, is_active)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING *;
    """, (schedule.name, schedule.time_of_day, days_str, AUTO_STOP_INTERVAL_SECONDS, 1, schedule.is_active))
    row = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()

    return {
        "id": row["id"],
        "name": row["name"],
        "time_of_day": row["time_of_day"],
        "days_of_week": schedule.days_of_week,
        "duration_seconds": AUTO_STOP_INTERVAL_SECONDS,
        "relay": 1,
        "is_active": bool(row["is_active"]),
        "created_at": row["created_at"].isoformat()
    }


def toggle_schedule(schedule_id: int, is_active: bool) -> Dict[str, Any]:
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        UPDATE irrigation_schedules
        SET is_active = %s
        WHERE id = %s
        RETURNING *;
    """, (is_active, schedule_id))
    row = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()

    if not row:
        return {"success": False, "message": "Schedule not found"}

    return {"success": True, "id": row["id"], "is_active": bool(row["is_active"])}


def delete_schedule(schedule_id: int) -> Dict[str, Any]:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM irrigation_schedules WHERE id = %s;", (schedule_id,))
    conn.commit()
    cur.close()
    conn.close()
    return {"success": True, "message": f"Schedule {schedule_id} deleted."}


# --- History of Watering Query ---

def get_watering_history(limit: int = 50) -> List[Dict[str, Any]]:
    """Retrieves formatted history of past watering execution events."""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT * FROM irrigation_logs
        WHERE event_type IN ('manual_trigger', 'scheduled_trigger', 'auto_stop')
        ORDER BY created_at DESC
        LIMIT %s;
    """, (limit,))
    rows = cur.fetchall()
    cur.close()
    conn.close()

    history = []
    for r in rows:
        evt_type = r["event_type"]
        details = r.get("details") or {}
        
        source = "Manual Trigger"
        if evt_type == "scheduled_trigger":
            sched_name = details.get("schedule_name", "Automated Schedule")
            source = f"Scheduled: {sched_name}"
        elif evt_type == "auto_stop":
            source = "1-Min Auto Safety Cutoff"

        duration = r.get("duration_seconds") or 60
        status_str = "Auto-Stopped (60s)" if evt_type == "auto_stop" else "Completed (60s)"

        history.append({
            "id": r["id"],
            "device_id": r["device_id"],
            "event_type": evt_type,
            "source": source,
            "relay": 1,
            "duration_seconds": duration,
            "status": status_str,
            "triggered_at": r["created_at"].isoformat() if r.get("created_at") else None,
            "stopped_at": details.get("stopped_at") or details.get("cutoff_at"),
            "details": details
        })
    return history


def get_irrigation_logs(limit: int = 50) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT * FROM irrigation_logs
        ORDER BY created_at DESC
        LIMIT %s;
    """, (limit,))
    rows = cur.fetchall()
    cur.close()
    conn.close()

    logs = []
    for r in rows:
        logs.append({
            "id": r["id"],
            "device_id": r["device_id"],
            "event_type": r["event_type"],
            "topic": r.get("topic"),
            "details": r.get("details") or {},
            "duration_seconds": r.get("duration_seconds"),
            "created_at": r["created_at"].isoformat() if r.get("created_at") else None
        })
    return logs
