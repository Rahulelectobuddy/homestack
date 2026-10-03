import React from "react";
import NetWorthWidget from "../../components/NetWorthWidget";

export default function NetWorthPage() {
  return (
    <main style={{ padding: "2rem", maxWidth: "1250px", margin: "0 auto" }}>
      <div style={{ marginBottom: "1.5rem" }}>
        <a href="/" style={{ color: "#38bdf8", textDecoration: "none", fontSize: "0.9rem", fontWeight: 600 }}>
          ← Back to Main Dashboard
        </a>
      </div>
      <NetWorthWidget />
    </main>
  );
}
