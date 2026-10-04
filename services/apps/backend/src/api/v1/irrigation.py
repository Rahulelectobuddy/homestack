from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional

try:
    from core.irrigation import (
        DeviceStatusOut,
        TriggerWaterRequest,
        ScheduleCreate,
        ScheduleOut,
        WateringHistoryOut,
        IrrigationLogOut,
        get_device_status,
        trigger_water_relay1,
        stop_water_relay1,
        get_schedules,
        create_schedule,
        toggle_schedule,
        delete_schedule,
        get_watering_history,
        get_irrigation_logs,
        AUTO_STOP_INTERVAL_SECONDS
    )
except ImportError:
    from src.core.irrigation import (
        DeviceStatusOut,
        TriggerWaterRequest,
        ScheduleCreate,
        ScheduleOut,
        WateringHistoryOut,
        IrrigationLogOut,
        get_device_status,
        trigger_water_relay1,
        stop_water_relay1,
        get_schedules,
        create_schedule,
        toggle_schedule,
        delete_schedule,
        get_watering_history,
        get_irrigation_logs,
        AUTO_STOP_INTERVAL_SECONDS
    )

router = APIRouter(prefix="/api/v1/irrigation", tags=["Balcony Irrigation Engine"])


@router.get("/status", response_model=DeviceStatusOut)
async def get_status(device_id: str = Query("esp32-balcony-03", description="Target ESP32 Device ID")):
    """
    Returns live status, heartbeat (hbt), online status, current relay 1 state,
    and auto-stop safety interval parameters.
    """
    try:
        return get_device_status(device_id=device_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch device status: {str(e)}")


@router.post("/trigger")
async def trigger_water(payload: TriggerWaterRequest):
    """
    Triggers Relay 1 watering for Balcony Irrigation System.
    Note: Watering automatically stops after a 1-minute (60 seconds) interval.
    """
    try:
        res = trigger_water_relay1(
            duration_seconds=payload.duration_seconds or AUTO_STOP_INTERVAL_SECONDS,
            source="manual"
        )
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to trigger watering: {str(e)}")


@router.post("/stop")
async def stop_water():
    """
    Manually stops Relay 1 watering immediately.
    """
    try:
        return stop_water_relay1(reason="manual_user_stop")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop watering: {str(e)}")


@router.get("/history", response_model=List[WateringHistoryOut])
async def list_watering_history(limit: int = Query(50, ge=1, le=200)):
    """
    Retrieves history of past manual and scheduled watering runs with auto-cutoff verification.
    """
    try:
        return get_watering_history(limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve watering history: {str(e)}")


@router.get("/schedules", response_model=List[ScheduleOut])
async def list_schedules():
    """
    Retrieves all automated watering schedules.
    """
    try:
        return get_schedules()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve schedules: {str(e)}")


@router.post("/schedules", response_model=ScheduleOut)
async def add_schedule(schedule: ScheduleCreate):
    """
    Creates a new automated watering schedule.
    """
    try:
        return create_schedule(schedule)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create schedule: {str(e)}")


@router.put("/schedules/{schedule_id}/toggle")
async def toggle_schedule_state(schedule_id: int, is_active: bool = Query(..., description="Enable or disable schedule")):
    """
    Toggles active state of a watering schedule.
    """
    try:
        return toggle_schedule(schedule_id=schedule_id, is_active=is_active)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to toggle schedule: {str(e)}")


@router.delete("/schedules/{schedule_id}")
async def remove_schedule(schedule_id: int):
    """
    Deletes an automated watering schedule.
    """
    try:
        return delete_schedule(schedule_id=schedule_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete schedule: {str(e)}")


@router.get("/logs", response_model=List[IrrigationLogOut])
async def list_logs(limit: int = Query(50, ge=1, le=200)):
    """
    Retrieves raw telemetry, heartbeat, and trigger logs.
    """
    try:
        return get_irrigation_logs(limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve logs: {str(e)}")
