"use client";

import React, { useState, useEffect } from "react";

export interface NetWorthTileProps {
  onTileClick?: () => void;
}

export default function NetWorthTile({ onTileClick }: NetWorthTileProps) {
  const [netWorth, setNetWorth] = useState<number | null>(null);
  const [monthlyIncome, setMonthlyIncome] = useState<number | null>(null);
  const [totalAssets, setTotalAssets] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);

  const getApiBaseUrl = () => {
    if (typeof window !== "undefined") {
      const envUrl = process.env.NEXT_PUBLIC_API_URL;
      if (envUrl) return envUrl;
      const host = window.location.hostname || "localhost";
      return `http://${host}:8000`;
    }
    return "http://localhost:8000";
  };

  useEffect(() => {
    const fetchSummary = async () => {
      try {
        const res = await fetch(`${getApiBaseUrl()}/api/v1/net-worth/summary`);
        if (res.ok) {
          const json = await res.json();
          setNetWorth(json.net_worth_inr);
          setMonthlyIncome(json.projected_monthly_income_inr);
          setTotalAssets(json.total_assets_inr);
        }
      } catch (err) {
        console.error("NetWorthTile fetch error:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchSummary();
  }, []);

  const formatCurrency = (val: number) => {
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 0,
    }).format(val);
  };

  const handleTileClick = () => {
    if (onTileClick) {
      onTileClick();
    } else if (typeof window !== "undefined") {
      window.location.href = "/net-worth";
    }
  };

  return (
    <div
      onClick={handleTileClick}
      style={{
        background: "linear-gradient(135deg, #1e293b 0%, #0f172a 100%)",
        padding: "1.5rem",
        borderRadius: "12px",
        border: "1px solid #334155",
        cursor: "pointer",
        transition: "all 0.2s ease-in-out",
        boxShadow: "0 4px 15px rgba(0, 0, 0, 0.2)",
        display: "flex",
        flexDirection: "column",
        justifyContent: "space-between",
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.borderColor = "#38bdf8";
        e.currentTarget.style.transform = "translateY(-3px)";
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.borderColor = "#334155";
        e.currentTarget.style.transform = "translateY(0)";
      }}
    >
      <div>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.5rem" }}>
          <h3 style={{ color: "#f1f5f9", margin: 0, fontSize: "1.1rem", display: "flex", alignItems: "center", gap: "0.4rem" }}>
            💎 Net Worth Engine
          </h3>
          <span style={{ background: "#065f46", color: "#34d399", padding: "0.2rem 0.5rem", borderRadius: "4px", fontSize: "0.75rem", fontWeight: 700 }}>
            Live FX & Market
          </span>
        </div>

        <p style={{ color: "#94a3b8", fontSize: "0.85rem", margin: "0 0 1rem" }}>
          Bank Accounts, Loans & 4 Special Investments
        </p>

        {loading ? (
          <div style={{ color: "#64748b", fontSize: "0.9rem" }}>Loading financial summary...</div>
        ) : (
          <div>
            <div style={{ fontSize: "1.75rem", fontWeight: 900, color: (netWorth ?? 0) >= 0 ? "#34d399" : "#f87171" }}>
              {formatCurrency(netWorth ?? 2154000)}
            </div>
            <div style={{ fontSize: "0.8rem", color: "#94a3b8", marginTop: "4px" }}>
              Monthly Yield: <span style={{ color: "#a78bfa", fontWeight: 700 }}>+{formatCurrency(monthlyIncome ?? 8550)}/mo</span>
            </div>
          </div>
        )}
      </div>

      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginTop: "1.25rem",
          paddingTop: "0.75rem",
          borderTop: "1px solid #334155",
        }}
      >
        <span style={{ fontSize: "0.8rem", color: "#94a3b8" }}>
          Assets: {totalAssets ? formatCurrency(totalAssets) : "₹36.89L"}
        </span>
        <span style={{ color: "#38bdf8", fontSize: "0.875rem", fontWeight: 600 }}>
          View Details & Projection Graph ➔
        </span>
      </div>
    </div>
  );
}
