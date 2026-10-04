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

export default function BalconyIrrigationTile() {
  const [status, setStatus] = useState<DeviceStatus | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [triggering, setTriggering] = useState<boolean>(false);
  const [countdown, setCountdown] = useState<number>(0);

  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://192.168.1.29:8000";

  const fetchStatus = async () => {
    try {
      const res = await fetch(`${API_URL}/api/v1/irrigation/status`);
      if (res.ok) {
        const data: DeviceStatus = await res.json();
        setStatus(data);
        if (data.watering_active && data.remaining_watering_seconds > 0) {
          setCountdown(data.remaining_watering_seconds);
        } else {
          setCountdown(0);
        }
      }
    } catch (err) {
      console.error("Error fetching irrigation status:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 4000);
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
        fetchStatus();
      }
    } catch (err) {
      console.error("Error triggering water:", err);
    } finally {
      setTriggering(false);
    }
  };

  const isOnline = status?.is_online ?? true;
  const isWatering = status?.watering_active || countdown > 0;

  return (
    <div
      style={{
        background: "linear-gradient(145deg, #1e293b 0%, #0f172a 100%)",
        padding: "1.5rem",
        borderRadius: "14px",
        border: "1px solid #334155",
        boxShadow: "0 4px 20px rgba(0, 0, 0, 0.25)",
        display: "flex",
        flexDirection: "column",
        justifyContent: "space-between",
        gap: "1rem",
      }}
    >
      <div>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.75rem" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
            <span style={{ fontSize: "1.25rem" }}>🌱</span>
            <h3 style={{ color: "#f8fafc", margin: 0, fontSize: "1.1rem", fontWeight: 700 }}>
              Balcony Irrigation
            </h3>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: "0.35rem" }}>
            <span
              style={{
                width: "8px",
                height: "8px",
                borderRadius: "50%",
                backgroundColor: isWatering ? "#38bdf8" : isOnline ? "#34d399" : "#f87171",
                boxShadow: isWatering
                  ? "0 0 8px #38bdf8"
                  : isOnline
                  ? "0 0 8px #34d399"
                  : "0 0 8px #f87171",
              }}
            />
            <span
              style={{
                fontSize: "0.75rem",
                fontWeight: 600,
                color: isWatering ? "#38bdf8" : isOnline ? "#34d399" : "#f87171",
                textTransform: "uppercase",
                letterSpacing: "0.05em",
              }}
            >
              {isWatering ? "WATERING" : isOnline ? "ONLINE (HBT)" : "OFFLINE"}
            </span>
          </div>
        </div>

        <p style={{ color: "#94a3b8", fontSize: "0.85rem", margin: "0 0 1rem 0" }}>
          ESP32 Project 03 • Soil Moisture & Relay 1 Controller
        </p>

        {/* Telemetry quick stats */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.75rem", marginBottom: "1rem" }}>
          <div style={{ background: "#0f172a", padding: "0.75rem", borderRadius: "8px", border: "1px solid #1e293b" }}>
            <span style={{ color: "#64748b", fontSize: "0.75rem", display: "block" }}>Soil Moisture</span>
            <span style={{ color: "#38bdf8", fontSize: "1.1rem", fontWeight: 700 }}>
              {status ? `${status.soil_moisture.toFixed(1)}%` : "48.0%"}
            </span>
          </div>
          <div style={{ background: "#0f172a", padding: "0.75rem", borderRadius: "8px", border: "1px solid #1e293b" }}>
            <span style={{ color: "#64748b", fontSize: "0.75rem", display: "block" }}>Relay 1 State</span>
            <span style={{ color: isWatering ? "#34d399" : "#cbd5e1", fontSize: "1.1rem", fontWeight: 700 }}>
              {isWatering ? `ON (${countdown}s)` : "OFF"}
            </span>
          </div>
        </div>

        {/* Safety Note Badge */}
        <div
          style={{
            background: "rgba(56, 189, 248, 0.08)",
            border: "1px solid rgba(56, 189, 248, 0.2)",
            borderRadius: "6px",
            padding: "0.5rem 0.75rem",
            fontSize: "0.75rem",
            color: "#7dd3fc",
            display: "flex",
            alignItems: "center",
            gap: "0.5rem",
          }}
        >
          <span>ℹ️</span>
          <span>Watering automatically stops after 1 min interval (60s safety cutoff).</span>
        </div>
      </div>

      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: "0.5rem" }}>
        <button
          onClick={handleTriggerWater}
          disabled={triggering || isWatering}
          style={{
            background: isWatering ? "#0284c7" : "linear-gradient(135deg, #0284c7 0%, #0369a1 100%)",
            color: "#ffffff",
            border: "none",
            borderRadius: "8px",
            padding: "0.5rem 1rem",
            fontSize: "0.85rem",
            fontWeight: 600,
            cursor: isWatering ? "not-allowed" : "pointer",
            boxShadow: "0 2px 8px rgba(2, 132, 199, 0.3)",
            transition: "all 0.2s ease",
            opacity: triggering ? 0.7 : 1,
          }}
        >
          {isWatering ? `💧 Watering (${countdown}s)` : triggering ? "Triggering..." : "💧 Water Relay 1"}
        </button>

        <a
          href="/irrigation"
          style={{
            color: "#38bdf8",
            textDecoration: "none",
            fontSize: "0.85rem",
            fontWeight: 600,
            display: "flex",
            alignItems: "center",
            gap: "0.25rem",
          }}
        >
          Dashboard & Schedules ➔
        </a>
      </div>
    </div>
  );
}
