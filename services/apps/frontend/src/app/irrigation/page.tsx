"use client";

import React, { useState, useEffect } from "react";

interface DeviceStatus {
  device_id: string;
  device_name: string;
  status: string;
  hbt: string | null;
  last_seen_seconds_ago: number;
  is_online: boolean;
  relay1_state: string;
  soil_moisture: number;
  temperature: number;
  rssi: number;
  watering_active: boolean;
  remaining_watering_seconds: number;
  auto_stop_interval_seconds: number;
  note: string;
}

interface Schedule {
  id: number;
  name: string;
  time_of_day: string;
  days_of_week: string[];
  duration_seconds: number;
  relay: number;
  is_active: boolean;
  last_run: string | null;
  created_at: string;
}

interface IrrigationLog {
  id: number;
  device_id: string;
  event_type: string;
  topic: string | null;
  details: any;
  duration_seconds: number | null;
  created_at: string;
}

export default function IrrigationDashboard() {
  const [status, setStatus] = useState<DeviceStatus | null>(null);
  const [schedules, setSchedules] = useState<Schedule[]>([]);
  const [logs, setLogs] = useState<IrrigationLog[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [triggering, setTriggering] = useState<boolean>(false);
  const [countdown, setCountdown] = useState<number>(0);

  // New Schedule Form state
  const [showAddModal, setShowAddModal] = useState<boolean>(false);
  const [newSchedName, setNewSchedName] = useState<string>("Balcony Refresh");
  const [newSchedTime, setNewSchedTime] = useState<string>("08:00");
  const [selectedDays, setSelectedDays] = useState<string[]>([
    "Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"
  ]);

  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://192.168.1.29:8000";

  const fetchStatus = async () => {
    try {
      const res = await fetch(`${API_URL}/api/v1/irrigation/status`);
      if (res.ok) {
        const data: DeviceStatus = await res.json();
        setStatus(data);
        if (data.watering_active && data.remaining_watering_seconds > 0) {
          setCountdown(data.remaining_watering_seconds);
        } else if (!data.watering_active) {
          setCountdown(0);
        }
      }
    } catch (err) {
      console.error("Failed to fetch irrigation status:", err);
    }
  };

  const fetchSchedules = async () => {
    try {
      const res = await fetch(`${API_URL}/api/v1/irrigation/schedules`);
      if (res.ok) {
        const data: Schedule[] = await res.json();
        setSchedules(data);
      }
    } catch (err) {
      console.error("Failed to fetch schedules:", err);
    }
  };

  const fetchLogs = async () => {
    try {
      const res = await fetch(`${API_URL}/api/v1/irrigation/logs?limit=30`);
      if (res.ok) {
        const data: IrrigationLog[] = await res.json();
        setLogs(data);
      }
    } catch (err) {
      console.error("Failed to fetch logs:", err);
    }
  };

  useEffect(() => {
    const init = async () => {
      setLoading(true);
      await Promise.all([fetchStatus(), fetchSchedules(), fetchLogs()]);
      setLoading(false);
    };
    init();

    const interval = setInterval(() => {
      fetchStatus();
      fetchLogs();
    }, 4000);

    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    let timer: any;
    if (countdown > 0) {
      timer = setInterval(() => {
        setCountdown((prev) => (prev > 1 ? prev - 1 : 0));
      }, 1000);
    }
    return () => clearInterval(timer);
  }, [countdown]);

  const handleTriggerWater = async () => {
    try {
      setTriggering(true);
      const res = await fetch(`${API_URL}/api/v1/irrigation/trigger`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ relay: 1, duration_seconds: 60 }),
      });
      if (res.ok) {
        setCountdown(60);
        await Promise.all([fetchStatus(), fetchLogs()]);
      }
    } catch (err) {
      console.error("Failed to trigger water:", err);
    } finally {
      setTriggering(false);
    }
  };

  const handleStopWater = async () => {
    try {
      const res = await fetch(`${API_URL}/api/v1/irrigation/stop`, {
        method: "POST",
      });
      if (res.ok) {
        setCountdown(0);
        await Promise.all([fetchStatus(), fetchLogs()]);
      }
    } catch (err) {
      console.error("Failed to stop water:", err);
    }
  };

  const handleToggleSchedule = async (id: number, currentActive: boolean) => {
    try {
      const res = await fetch(
        `${API_URL}/api/v1/irrigation/schedules/${id}/toggle?is_active=${!currentActive}`,
        { method: "PUT" }
      );
      if (res.ok) {
        fetchSchedules();
      }
    } catch (err) {
      console.error("Failed to toggle schedule:", err);
    }
  };

  const handleDeleteSchedule = async (id: number) => {
    try {
      const res = await fetch(`${API_URL}/api/v1/irrigation/schedules/${id}`, {
        method: "DELETE",
      });
      if (res.ok) {
        fetchSchedules();
      }
    } catch (err) {
      console.error("Failed to delete schedule:", err);
    }
  };

  const handleCreateSchedule = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await fetch(`${API_URL}/api/v1/irrigation/schedules`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: newSchedName,
          time_of_day: newSchedTime,
          days_of_week: selectedDays,
          duration_seconds: 60,
          is_active: true,
        }),
      });
      if (res.ok) {
        setShowAddModal(false);
        fetchSchedules();
      }
    } catch (err) {
      console.error("Failed to create schedule:", err);
    }
  };

  const toggleDaySelection = (day: string) => {
    setSelectedDays((prev) =>
      prev.includes(day) ? prev.filter((d) => d !== day) : [...prev, day]
    );
  };

  const isOnline = status?.is_online ?? true;
  const isWatering = status?.watering_active || countdown > 0;
  const soilMoisture = status?.soil_moisture ?? 48.0;

  return (
    <main style={{ padding: "2rem", maxWidth: "1280px", margin: "0 auto" }}>
      {/* Top Header */}
      <header
        style={{
          marginBottom: "2rem",
          borderBottom: "1px solid #334155",
          paddingBottom: "1rem",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: "1rem",
        }}
      >
        <div>
          <a
            href="/"
            style={{
              color: "#38bdf8",
              textDecoration: "none",
              fontSize: "0.875rem",
              fontWeight: 600,
              display: "inline-block",
              marginBottom: "0.5rem",
            }}
          >
            ← Back to Homelab Dashboard
          </a>
          <h1 style={{ color: "#f8fafc", margin: 0, fontSize: "1.75rem", display: "flex", alignItems: "center", gap: "0.5rem" }}>
            🌱 Balcony Irrigation Controller
          </h1>
          <p style={{ color: "#94a3b8", margin: "0.25rem 0 0 0" }}>
            ESP32 Workspace Project 03 • MQTT Telemetry, Relay 1 Actuation & 1-Min Auto-Stop Guard
          </p>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
          <div
            style={{
              background: "#1e293b",
              padding: "0.5rem 1rem",
              borderRadius: "8px",
              border: "1px solid #334155",
              display: "flex",
              alignItems: "center",
              gap: "0.5rem",
            }}
          >
            <span
              style={{
                width: "10px",
                height: "10px",
                borderRadius: "50%",
                backgroundColor: isOnline ? "#34d399" : "#f87171",
                boxShadow: isOnline ? "0 0 10px #34d399" : "0 0 10px #f87171",
              }}
            />
            <span style={{ fontSize: "0.875rem", fontWeight: 600, color: "#f1f5f9" }}>
              {isOnline ? "ESP32 ONLINE (HBT)" : "ESP32 OFFLINE"}
            </span>
          </div>

          <div
            style={{
              background: "rgba(56, 189, 248, 0.1)",
              border: "1px solid rgba(56, 189, 248, 0.3)",
              padding: "0.5rem 1rem",
              borderRadius: "8px",
              color: "#38bdf8",
              fontSize: "0.875rem",
              fontWeight: 600,
            }}
          >
            MQTT: homelab/irrigation/#
          </div>
        </div>
      </header>

      {/* Grid Layout for Panels */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(360px, 1fr))", gap: "1.5rem", marginBottom: "2rem" }}>
        
        {/* Panel 1: Device Telemetry & Heartbeat (HBT) Status */}
        <div
          style={{
            background: "#1e293b",
            padding: "1.5rem",
            borderRadius: "14px",
            border: "1px solid #334155",
            boxShadow: "0 4px 15px rgba(0,0,0,0.2)",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1.25rem" }}>
            <h2 style={{ color: "#f8fafc", margin: 0, fontSize: "1.2rem", fontWeight: 700 }}>
              📡 Device Telemetry & HBT
            </h2>
            <span style={{ color: "#94a3b8", fontSize: "0.8rem" }}>ID: esp32-balcony-03</span>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem", marginBottom: "1.25rem" }}>
            {/* Soil Moisture Metric */}
            <div style={{ background: "#0f172a", padding: "1rem", borderRadius: "10px", border: "1px solid #1e293b" }}>
              <span style={{ color: "#94a3b8", fontSize: "0.8rem", display: "block", marginBottom: "0.25rem" }}>
                Soil Moisture
              </span>
              <div style={{ fontSize: "1.6rem", fontWeight: 800, color: soilMoisture < 35 ? "#fbbf24" : "#38bdf8" }}>
                {soilMoisture.toFixed(1)}%
              </div>
              <div style={{ width: "100%", background: "#334155", height: "6px", borderRadius: "3px", marginTop: "0.5rem" }}>
                <div
                  style={{
                    width: `${Math.min(100, Math.max(0, soilMoisture))}%`,
                    background: soilMoisture < 35 ? "#fbbf24" : "#38bdf8",
                    height: "100%",
                    borderRadius: "3px",
                    transition: "width 0.5s ease",
                  }}
                />
              </div>
            </div>

            {/* Temperature Metric */}
            <div style={{ background: "#0f172a", padding: "1rem", borderRadius: "10px", border: "1px solid #1e293b" }}>
              <span style={{ color: "#94a3b8", fontSize: "0.8rem", display: "block", marginBottom: "0.25rem" }}>
                Temperature
              </span>
              <div style={{ fontSize: "1.6rem", fontWeight: 800, color: "#f43f5e" }}>
                {status?.temperature ? `${status.temperature.toFixed(1)}°C` : "26.5°C"}
              </div>
              <span style={{ color: "#64748b", fontSize: "0.75rem", display: "block", marginTop: "0.5rem" }}>
                Signal: {status?.rssi ?? -65} dBm
              </span>
            </div>
          </div>

          {/* Heartbeat Detail Bar */}
          <div style={{ background: "#0f172a", padding: "0.875rem 1rem", borderRadius: "10px", border: "1px solid #1e293b" }}>
            <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.85rem", color: "#cbd5e1" }}>
              <span>Heartbeat (HBT) Status:</span>
              <span style={{ color: "#34d399", fontWeight: 600 }}>
                {status ? `Received ${status.last_seen_seconds_ago}s ago` : "Active"}
              </span>
            </div>
            <div style={{ fontSize: "0.75rem", color: "#64748b", marginTop: "0.35rem" }}>
              Last HBT Timestamp: {status?.hbt ? new Date(status.hbt).toLocaleTimeString() : "Just now"}
            </div>
          </div>
        </div>

        {/* Panel 2: Relay 1 Water Control & 1-Min Auto-Stop Safety Guard */}
        <div
          style={{
            background: "#1e293b",
            padding: "1.5rem",
            borderRadius: "14px",
            border: "1px solid #334155",
            boxShadow: "0 4px 15px rgba(0,0,0,0.2)",
            display: "flex",
            flexDirection: "column",
            justifyContent: "space-between",
          }}
        >
          <div>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }}>
              <h2 style={{ color: "#f8fafc", margin: 0, fontSize: "1.2rem", fontWeight: 700 }}>
                ⚡ Relay 1 Water Actuator
              </h2>
              <span
                style={{
                  background: isWatering ? "rgba(52, 211, 153, 0.15)" : "rgba(148, 163, 184, 0.15)",
                  color: isWatering ? "#34d399" : "#94a3b8",
                  padding: "0.25rem 0.65rem",
                  borderRadius: "6px",
                  fontSize: "0.75rem",
                  fontWeight: 700,
                  textTransform: "uppercase",
                }}
              >
                Relay 1: {isWatering ? "ACTIVE (ON)" : "IDLE (OFF)"}
              </span>
            </div>

            {/* Countdown / Status display */}
            <div
              style={{
                background: isWatering ? "rgba(14, 165, 233, 0.1)" : "#0f172a",
                border: isWatering ? "1px solid #0284c7" : "1px solid #1e293b",
                borderRadius: "10px",
                padding: "1rem",
                textAlign: "center",
                marginBottom: "1.25rem",
              }}
            >
              {isWatering ? (
                <div>
                  <span style={{ color: "#38bdf8", fontSize: "0.85rem", fontWeight: 600, display: "block" }}>
                    🌊 WATERING IN PROGRESS
                  </span>
                  <div style={{ fontSize: "2.5rem", fontWeight: 900, color: "#38bdf8", margin: "0.25rem 0" }}>
                    {countdown}s
                  </div>
                  <span style={{ color: "#94a3b8", fontSize: "0.75rem" }}>
                    Auto-stop cutoff in {countdown} seconds
                  </span>
                </div>
              ) : (
                <div>
                  <span style={{ color: "#94a3b8", fontSize: "0.85rem", display: "block" }}>
                    Valve Ready for Water Cycle
                  </span>
                  <div style={{ fontSize: "1.2rem", fontWeight: 700, color: "#cbd5e1", margin: "0.5rem 0" }}>
                    Interval: 1 Minute (60s)
                  </div>
                </div>
              )}
            </div>

            {/* Prominent 1-Min Auto-Stop Safety Callout */}
            <div
              style={{
                background: "linear-gradient(135deg, rgba(30, 58, 138, 0.3) 0%, rgba(15, 23, 42, 0.5) 100%)",
                border: "1px solid rgba(59, 130, 246, 0.3)",
                borderRadius: "10px",
                padding: "0.875rem 1rem",
                marginBottom: "1.25rem",
              }}
            >
              <div style={{ display: "flex", gap: "0.6rem", alignItems: "flex-start" }}>
                <span style={{ fontSize: "1.1rem" }}>🛡️</span>
                <div>
                  <h4 style={{ color: "#60a5fa", margin: "0 0 0.2rem 0", fontSize: "0.875rem", fontWeight: 700 }}>
                    1-Minute Safety Cutoff Active
                  </h4>
                  <p style={{ color: "#93c5fd", margin: 0, fontSize: "0.78rem", lineHeight: 1.4 }}>
                    To prevent root rot and balcony overflow, all Relay 1 watering operations automatically execute for a <strong>1-minute (60 seconds) interval</strong> and auto-shut down.
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Buttons */}
          <div style={{ display: "flex", gap: "0.75rem" }}>
            <button
              onClick={handleTriggerWater}
              disabled={triggering || isWatering}
              style={{
                flex: 1,
                background: isWatering ? "#0369a1" : "linear-gradient(135deg, #0284c7 0%, #0369a1 100%)",
                color: "#ffffff",
                border: "none",
                borderRadius: "10px",
                padding: "0.85rem",
                fontSize: "0.95rem",
                fontWeight: 700,
                cursor: isWatering ? "not-allowed" : "pointer",
                boxShadow: "0 4px 12px rgba(2, 132, 199, 0.3)",
                opacity: triggering ? 0.7 : 1,
              }}
            >
              {isWatering ? `💧 Watering (${countdown}s)` : triggering ? "Actuation Sent..." : "💧 Trigger Water (Relay 1)"}
            </button>

            {isWatering && (
              <button
                onClick={handleStopWater}
                style={{
                  background: "#be123c",
                  color: "#ffffff",
                  border: "none",
                  borderRadius: "10px",
                  padding: "0.85rem 1.25rem",
                  fontSize: "0.9rem",
                  fontWeight: 700,
                  cursor: "pointer",
                }}
              >
                🛑 Stop
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Section 2: Automated Watering Schedules */}
      <section
        style={{
          background: "#1e293b",
          padding: "1.5rem",
          borderRadius: "14px",
          border: "1px solid #334155",
          marginBottom: "2rem",
          boxShadow: "0 4px 15px rgba(0,0,0,0.2)",
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1.25rem", flexWrap: "wrap", gap: "1rem" }}>
          <div>
            <h2 style={{ color: "#f8fafc", margin: 0, fontSize: "1.25rem", fontWeight: 700, display: "flex", alignItems: "center", gap: "0.5rem" }}>
              ⏰ Scheduled Balcony Watering
            </h2>
            <p style={{ color: "#94a3b8", margin: "0.25rem 0 0 0", fontSize: "0.85rem" }}>
              Automated cron timers triggering Relay 1 for 1-minute intervals
            </p>
          </div>

          <button
            onClick={() => setShowAddModal(true)}
            style={{
              background: "#10b981",
              color: "#ffffff",
              border: "none",
              borderRadius: "8px",
              padding: "0.6rem 1.1rem",
              fontSize: "0.875rem",
              fontWeight: 700,
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              gap: "0.35rem",
            }}
          >
            ➕ Add New Schedule
          </button>
        </div>

        {/* Schedule List */}
        {schedules.length === 0 ? (
          <div style={{ padding: "2rem", textAlign: "center", color: "#64748b", background: "#0f172a", borderRadius: "10px" }}>
            No automated schedules configured. Click "Add New Schedule" to create one.
          </div>
        ) : (
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))", gap: "1rem" }}>
            {schedules.map((sched) => (
              <div
                key={sched.id}
                style={{
                  background: "#0f172a",
                  padding: "1.25rem",
                  borderRadius: "10px",
                  border: sched.is_active ? "1px solid #3b82f6" : "1px solid #334155",
                  display: "flex",
                  flexDirection: "column",
                  justifyContent: "space-between",
                  gap: "1rem",
                }}
              >
                <div>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "0.5rem" }}>
                    <h3 style={{ color: "#f1f5f9", margin: 0, fontSize: "1.05rem", fontWeight: 700 }}>
                      {sched.name}
                    </h3>
                    <span
                      style={{
                        background: sched.is_active ? "rgba(16, 185, 129, 0.15)" : "rgba(148, 163, 184, 0.15)",
                        color: sched.is_active ? "#34d399" : "#94a3b8",
                        padding: "0.2rem 0.5rem",
                        borderRadius: "4px",
                        fontSize: "0.75rem",
                        fontWeight: 600,
                      }}
                    >
                      {sched.is_active ? "ACTIVE" : "PAUSED"}
                    </span>
                  </div>

                  <div style={{ fontSize: "1.6rem", fontWeight: 800, color: "#38bdf8", marginBottom: "0.5rem" }}>
                    {sched.time_of_day}
                  </div>

                  <div style={{ display: "flex", flexWrap: "wrap", gap: "0.35rem", marginBottom: "0.75rem" }}>
                    {["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"].map((day) => {
                      const isSel = sched.days_of_week.includes(day);
                      return (
                        <span
                          key={day}
                          style={{
                            fontSize: "0.7rem",
                            padding: "0.15rem 0.4rem",
                            borderRadius: "4px",
                            background: isSel ? "#1e3a8a" : "#1e293b",
                            color: isSel ? "#93c5fd" : "#475569",
                            fontWeight: isSel ? 700 : 400,
                          }}
                        >
                          {day}
                        </span>
                      );
                    })}
                  </div>

                  <div style={{ fontSize: "0.78rem", color: "#94a3b8" }}>
                    Duration: <strong>1 Minute (60s)</strong> • Relay: 1
                  </div>
                  {sched.last_run && (
                    <div style={{ fontSize: "0.75rem", color: "#64748b", marginTop: "0.25rem" }}>
                      Last Executed: {new Date(sched.last_run).toLocaleString()}
                    </div>
                  )}
                </div>

                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", borderTop: "1px solid #1e293b", paddingTop: "0.75rem" }}>
                  <button
                    onClick={() => handleToggleSchedule(sched.id, sched.is_active)}
                    style={{
                      background: "transparent",
                      color: sched.is_active ? "#fbbf24" : "#34d399",
                      border: `1px solid ${sched.is_active ? "#fbbf24" : "#34d399"}`,
                      borderRadius: "6px",
                      padding: "0.35rem 0.75rem",
                      fontSize: "0.78rem",
                      fontWeight: 600,
                      cursor: "pointer",
                    }}
                  >
                    {sched.is_active ? "Pause" : "Enable"}
                  </button>

                  <button
                    onClick={() => handleDeleteSchedule(sched.id)}
                    style={{
                      background: "transparent",
                      color: "#f43f5e",
                      border: "none",
                      fontSize: "0.78rem",
                      fontWeight: 600,
                      cursor: "pointer",
                    }}
                  >
                    Delete 🗑️
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Section 3: Live Telemetry & Event History Logs */}
      <section
        style={{
          background: "#1e293b",
          padding: "1.5rem",
          borderRadius: "14px",
          border: "1px solid #334155",
          boxShadow: "0 4px 15px rgba(0,0,0,0.2)",
        }}
      >
        <h2 style={{ color: "#f8fafc", margin: "0 0 1rem 0", fontSize: "1.25rem", fontWeight: 700 }}>
          📋 Live Event & Heartbeat Logs
        </h2>

        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.85rem", color: "#cbd5e1" }}>
            <thead>
              <tr style={{ borderBottom: "1px solid #334155", textAlign: "left" }}>
                <th style={{ padding: "0.75rem", color: "#94a3b8" }}>Timestamp</th>
                <th style={{ padding: "0.75rem", color: "#94a3b8" }}>Event Type</th>
                <th style={{ padding: "0.75rem", color: "#94a3b8" }}>Topic</th>
                <th style={{ padding: "0.75rem", color: "#94a3b8" }}>Duration</th>
                <th style={{ padding: "0.75rem", color: "#94a3b8" }}>Details</th>
              </tr>
            </thead>
            <tbody>
              {logs.length === 0 ? (
                <tr>
                  <td colSpan={5} style={{ padding: "1.5rem", textAlign: "center", color: "#64748b" }}>
                    No logs recorded yet.
                  </td>
                </tr>
              ) : (
                logs.map((log) => (
                  <tr key={log.id} style={{ borderBottom: "1px solid #1e293b" }}>
                    <td style={{ padding: "0.65rem 0.75rem", color: "#94a3b8" }}>
                      {log.created_at ? new Date(log.created_at).toLocaleTimeString() : "-"}
                    </td>
                    <td style={{ padding: "0.65rem 0.75rem" }}>
                      <span
                        style={{
                          padding: "0.15rem 0.5rem",
                          borderRadius: "4px",
                          fontSize: "0.75rem",
                          fontWeight: 700,
                          background:
                            log.event_type.includes("trigger")
                              ? "rgba(56, 189, 248, 0.15)"
                              : log.event_type.includes("auto_stop")
                              ? "rgba(251, 191, 36, 0.15)"
                              : "rgba(148, 163, 184, 0.15)",
                          color:
                            log.event_type.includes("trigger")
                              ? "#38bdf8"
                              : log.event_type.includes("auto_stop")
                              ? "#fbbf24"
                              : "#94a3b8",
                        }}
                      >
                        {log.event_type}
                      </span>
                    </td>
                    <td style={{ padding: "0.65rem 0.75rem", color: "#64748b", fontFamily: "monospace" }}>
                      {log.topic || "homelab/irrigation/#"}
                    </td>
                    <td style={{ padding: "0.65rem 0.75rem", fontWeight: 600 }}>
                      {log.duration_seconds ? `${log.duration_seconds}s (1 min)` : "-"}
                    </td>
                    <td style={{ padding: "0.65rem 0.75rem", color: "#e2e8f0", fontSize: "0.8rem" }}>
                      {JSON.stringify(log.details)}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </section>

      {/* Add Schedule Modal */}
      {showAddModal && (
        <div
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: "rgba(0,0,0,0.75)",
            backdropFilter: "blur(4px)",
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            zIndex: 1000,
          }}
        >
          <div
            style={{
              background: "#1e293b",
              border: "1px solid #334155",
              borderRadius: "14px",
              padding: "1.75rem",
              width: "100%",
              maxWidth: "480px",
              boxShadow: "0 10px 30px rgba(0,0,0,0.5)",
            }}
          >
            <h3 style={{ color: "#f8fafc", margin: "0 0 1rem 0", fontSize: "1.2rem", fontWeight: 700 }}>
              ➕ Create Automated Watering Schedule
            </h3>

            <form onSubmit={handleCreateSchedule}>
              <div style={{ marginBottom: "1rem" }}>
                <label style={{ color: "#cbd5e1", fontSize: "0.85rem", display: "block", marginBottom: "0.35rem" }}>
                  Schedule Name
                </label>
                <input
                  type="text"
                  value={newSchedName}
                  onChange={(e) => setNewSchedName(e.target.value)}
                  required
                  style={{
                    width: "100%",
                    padding: "0.65rem",
                    borderRadius: "8px",
                    background: "#0f172a",
                    border: "1px solid #334155",
                    color: "#f8fafc",
                    fontSize: "0.9rem",
                    boxSizing: "border-box",
                  }}
                />
              </div>

              <div style={{ marginBottom: "1rem" }}>
                <label style={{ color: "#cbd5e1", fontSize: "0.85rem", display: "block", marginBottom: "0.35rem" }}>
                  Watering Time (24-Hour HH:MM)
                </label>
                <input
                  type="time"
                  value={newSchedTime}
                  onChange={(e) => setNewSchedTime(e.target.value)}
                  required
                  style={{
                    width: "100%",
                    padding: "0.65rem",
                    borderRadius: "8px",
                    background: "#0f172a",
                    border: "1px solid #334155",
                    color: "#f8fafc",
                    fontSize: "0.9rem",
                    boxSizing: "border-box",
                  }}
                />
              </div>

              <div style={{ marginBottom: "1.25rem" }}>
                <label style={{ color: "#cbd5e1", fontSize: "0.85rem", display: "block", marginBottom: "0.5rem" }}>
                  Days of Week
                </label>
                <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem" }}>
                  {["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"].map((day) => {
                    const isSel = selectedDays.includes(day);
                    return (
                      <button
                        key={day}
                        type="button"
                        onClick={() => toggleDaySelection(day)}
                        style={{
                          padding: "0.4rem 0.75rem",
                          borderRadius: "6px",
                          border: isSel ? "1px solid #3b82f6" : "1px solid #334155",
                          background: isSel ? "#1e3a8a" : "#0f172a",
                          color: isSel ? "#93c5fd" : "#94a3b8",
                          fontWeight: isSel ? 700 : 400,
                          cursor: "pointer",
                          fontSize: "0.8rem",
                        }}
                      >
                        {day}
                      </button>
                    );
                  })}
                </div>
              </div>

              <div
                style={{
                  background: "rgba(56, 189, 248, 0.08)",
                  border: "1px solid rgba(56, 189, 248, 0.2)",
                  borderRadius: "8px",
                  padding: "0.75rem",
                  marginBottom: "1.25rem",
                  fontSize: "0.78rem",
                  color: "#7dd3fc",
                }}
              >
                ℹ️ Duration is automatically set to <strong>1 minute (60 seconds)</strong> for safety.
              </div>

              <div style={{ display: "flex", justifyContent: "flex-end", gap: "0.75rem" }}>
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  style={{
                    background: "transparent",
                    color: "#94a3b8",
                    border: "1px solid #334155",
                    borderRadius: "8px",
                    padding: "0.6rem 1rem",
                    fontSize: "0.85rem",
                    fontWeight: 600,
                    cursor: "pointer",
                  }}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  style={{
                    background: "#10b981",
                    color: "#ffffff",
                    border: "none",
                    borderRadius: "8px",
                    padding: "0.6rem 1.25rem",
                    fontSize: "0.85rem",
                    fontWeight: 700,
                    cursor: "pointer",
                  }}
                >
                  Save Schedule
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </main>
  );
}
