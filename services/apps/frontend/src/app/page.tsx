import React from "react";
import NetWorthTile from "../components/NetWorthTile";

export default function Home() {
  return (
    <main style={{ padding: "2rem", maxWidth: "1250px", margin: "0 auto" }}>
      <header style={{ marginBottom: "2rem", borderBottom: "1px solid #334155", paddingBottom: "1rem" }}>
        <h1 style={{ color: "#38bdf8", margin: 0 }}>Homelab Data Platform</h1>
        <p style={{ color: "#94a3b8" }}>Central financial engine, analytics, ingestion monitoring, and system metrics</p>
      </header>

      <h2 style={{ color: "#f8fafc", marginBottom: "1.25rem", fontSize: "1.25rem" }}>
        📊 Services & Financial Dashboards
      </h2>
      
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "1.5rem" }}>
        {/* Dashboard Tile for Net Worth Tracker & Financial Engine */}
        <NetWorthTile />

        <div style={{ background: "#1e293b", padding: "1.5rem", borderRadius: "12px", border: "1px solid #334155", display: "flex", flexDirection: "column", justifyContent: "space-between" }}>
          <div>
            <h3 style={{ color: "#f1f5f9", marginTop: 0 }}>Bus Fare Scraper</h3>
            <p style={{ color: "#94a3b8" }}>Status: Active (Pune ➔ Indore)</p>
          </div>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: "1.5rem" }}>
            <span style={{ background: "#065f46", color: "#34d399", padding: "0.25rem 0.5rem", borderRadius: "4px", fontSize: "0.875rem" }}>Healthy</span>
            <a href="/bus-fares" style={{ color: "#38bdf8", textDecoration: "none", fontSize: "0.875rem", fontWeight: 600 }}>
              View Analytics Dashboard ➔
            </a>
          </div>
        </div>

        <div style={{ background: "#1e293b", padding: "1.5rem", borderRadius: "12px", border: "1px solid #334155" }}>
          <h3 style={{ color: "#f1f5f9", marginTop: 0 }}>Balcony Irrigation</h3>
          <p style={{ color: "#94a3b8" }}>Status: MQTT Listening</p>
          <span style={{ background: "#065f46", color: "#34d399", padding: "0.25rem 0.5rem", borderRadius: "4px", fontSize: "0.875rem" }}>Connected</span>
        </div>
        
        <div style={{ background: "#1e293b", padding: "1.5rem", borderRadius: "12px", border: "1px solid #334155" }}>
          <h3 style={{ color: "#f1f5f9", marginTop: 0 }}>Android Health Stats</h3>
          <p style={{ color: "#94a3b8" }}>Status: Ingesting</p>
          <span style={{ background: "#065f46", color: "#34d399", padding: "0.25rem 0.5rem", borderRadius: "4px", fontSize: "0.875rem" }}>Ready</span>
        </div>
      </div>
    </main>
  );
}
