"use client";

import React, { useState, useEffect } from "react";
import NetWorthManagerModal, { AccountBalance, SpecialAssetHolding } from "./NetWorthManagerModal";
import ProjectionChart from "./ProjectionChart";


export interface NetWorthSummaryData {
  net_worth_inr: number;
  total_assets_inr: number;
  total_liabilities_inr: number;
  total_account_assets_inr: number;
  special_investments_inr: number;
  projected_monthly_income_inr: number;
  usd_inr_rate: number;
  special_investments_breakdown: SpecialAssetHolding[];
  accounts: AccountBalance[];
  market_prices: {
    uber_usd: number;
    accenture_usd: number;
    usd_inr: number;
    gold_10g_inr: number;
    silver_1kg_inr: number;
    last_updated?: string;
  };
}

export default function NetWorthWidget() {
  const [data, setData] = useState<NetWorthSummaryData | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Helper to resolve API endpoint host
  const getApiBaseUrl = () => {
    if (typeof window !== "undefined") {
      const envUrl = process.env.NEXT_PUBLIC_API_URL;
      if (envUrl) return envUrl;
      // Fallback: assume backend running on port 8000 on same host or localhost
      const host = window.location.hostname || "localhost";
      return `http://${host}:8000`;
    }
    return "http://localhost:8000";
  };

  const fetchSummary = async () => {
    try {
      setError(null);
      const url = `${getApiBaseUrl()}/api/v1/net-worth/summary`;
      const res = await fetch(url);
      if (!res.ok) throw new Error(`HTTP error ${res.status}`);
      const json: NetWorthSummaryData = await res.json();
      setData(json);
    } catch (err: any) {
      console.error("Failed to fetch net worth summary:", err);
      setError("Unable to connect to financial engine backend.");
    } finally {
      setLoading(false);
    }
  };

  const handleRefreshPrices = async () => {
    try {
      setRefreshing(true);
      setError(null);
      const url = `${getApiBaseUrl()}/api/v1/net-worth/refresh`;
      const res = await fetch(url, { method: "POST" });
      if (!res.ok) throw new Error(`HTTP error ${res.status}`);
      const json: NetWorthSummaryData = await res.json();
      setData(json);
    } catch (err: any) {
      console.error("Failed to refresh market prices:", err);
      setError("Market refresh failed. Using cached rates.");
    } finally {
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchSummary();
  }, []);

  const handleAddAccount = async (acc: { account_name: string; account_type: "asset" | "liability"; balance_inr: number; monthly_return_pct: number }) => {
    const url = `${getApiBaseUrl()}/api/v1/net-worth/accounts`;
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(acc),
    });
    if (!res.ok) throw new Error("Failed to add account");
    await fetchSummary();
  };

  const handleDeleteAccount = async (id: number) => {
    const url = `${getApiBaseUrl()}/api/v1/net-worth/accounts/${id}`;
    const res = await fetch(url, { method: "DELETE" });
    if (!res.ok) throw new Error("Failed to delete account");
    await fetchSummary();
  };

  const handleUpdateSpecialAssets = async (holdings: { uber_stock: number; accenture_stock: number; gold_10g: number; silver_1kg: number }) => {
    const url = `${getApiBaseUrl()}/api/v1/net-worth/assets`;
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(holdings),
    });
    if (!res.ok) throw new Error("Failed to update assets");
    await fetchSummary();
  };

  const formatCurrency = (val: number) => {
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 0,
    }).format(val);
  };

  if (loading) {
    return (
      <div
        style={{
          background: "#0f172a",
          border: "1px solid #1e293b",
          borderRadius: "16px",
          padding: "2rem",
          color: "#94a3b8",
          textAlign: "center",
        }}
      >
        <div style={{ fontSize: "1.5rem", marginBottom: "0.5rem" }}>⌛ Loading Financial Engine...</div>
      </div>
    );
  }

  // Fallback demo data if backend connection fails
  const summary = data || {
    net_worth_inr: 2154000,
    total_assets_inr: 3689000,
    total_liabilities_inr: 1535000,
    total_account_assets_inr: 700000,
    special_investments_inr: 2989000,
    projected_monthly_income_inr: 8550,
    usd_inr_rate: 83.75,
    special_investments_breakdown: [
      { id: 1, asset_key: "uber_stock", asset_name: "Uber Technologies (UBER)", quantity: 15, unit_price_usd: 76.5, unit_price_inr: 6406.88, total_valuation_inr: 96103 },
      { id: 2, asset_key: "accenture_stock", asset_name: "Accenture plc (ACN)", quantity: 5, unit_price_usd: 348.2, unit_price_inr: 29161.75, total_valuation_inr: 145809 },
      { id: 3, asset_key: "gold_10g", asset_name: "Gold 24K (10-Gram units)", quantity: 2, unit_price_usd: null, unit_price_inr: 75500, total_valuation_inr: 151000 },
      { id: 4, asset_key: "silver_1kg", asset_name: "Silver (1-Kg units)", quantity: 1, unit_price_usd: null, unit_price_inr: 89000, total_valuation_inr: 89000 },
    ],
    accounts: [],
    market_prices: { uber_usd: 76.5, accenture_usd: 348.2, usd_inr: 83.75, gold_10g_inr: 75500, silver_1kg_inr: 89000 },
  };

  const getAssetDetails = (key: string) => {
    return summary.special_investments_breakdown.find((a) => a.asset_key === key);
  };

  const uber = getAssetDetails("uber_stock");
  const acn = getAssetDetails("accenture_stock");
  const gold = getAssetDetails("gold_10g");
  const silver = getAssetDetails("silver_1kg");

  return (
    <div
      style={{
        background: "linear-gradient(145deg, #0f172a 0%, #1e293b 100%)",
        border: "1px solid #334155",
        borderRadius: "20px",
        padding: "1.75rem",
        color: "#f8fafc",
        boxShadow: "0 10px 25px -5px rgba(0, 0, 0, 0.3)",
        margin: "1.5rem 0",
      }}
    >
      {/* Header Bar */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: "1rem",
          marginBottom: "1.5rem",
          borderBottom: "1px solid #334155",
          paddingBottom: "1rem",
        }}
      >
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
            <h2 style={{ margin: 0, fontSize: "1.5rem", fontWeight: 800, color: "#f8fafc" }}>
              💎 Net Worth & Financial Engine
            </h2>
            <span
              style={{
                background: "rgba(56, 189, 248, 0.15)",
                color: "#38bdf8",
                border: "1px solid #0284c7",
                padding: "0.2rem 0.6rem",
                borderRadius: "20px",
                fontSize: "0.75rem",
                fontWeight: 700,
              }}
            >
              Base: ₹ INR
            </span>
          </div>
          <p style={{ margin: "4px 0 0", fontSize: "0.85rem", color: "#94a3b8" }}>
            Live market prices • FX Rate: 1 USD = ₹{summary.usd_inr_rate}
          </p>
        </div>

        {/* Actions */}
        <div style={{ display: "flex", gap: "0.75rem" }}>
          <button
            onClick={handleRefreshPrices}
            disabled={refreshing}
            style={{
              background: refreshing ? "#475569" : "#0284c7",
              color: "#ffffff",
              border: "none",
              padding: "0.6rem 1.1rem",
              borderRadius: "10px",
              fontWeight: 700,
              fontSize: "0.875rem",
              cursor: refreshing ? "not-allowed" : "pointer",
              display: "flex",
              alignItems: "center",
              gap: "0.5rem",
              boxShadow: "0 4px 12px rgba(2, 132, 199, 0.3)",
              transition: "all 0.2s ease",
            }}
          >
            <span style={{ display: "inline-block", animation: refreshing ? "spin 1s linear infinite" : "none" }}>
              🔄
            </span>
            {refreshing ? "Refreshing..." : "Refresh Prices"}
          </button>

          <button
            onClick={() => setIsModalOpen(true)}
            style={{
              background: "#334155",
              color: "#f8fafc",
              border: "1px solid #475569",
              padding: "0.6rem 1.1rem",
              borderRadius: "10px",
              fontWeight: 700,
              fontSize: "0.875rem",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              gap: "0.5rem",
            }}
          >
            ⚙️ Manage Accounts & Assets
          </button>
        </div>
      </div>

      {error && (
        <div
          style={{
            background: "rgba(239, 68, 68, 0.15)",
            border: "1px solid #dc2626",
            color: "#f87171",
            padding: "0.75rem 1rem",
            borderRadius: "8px",
            fontSize: "0.875rem",
            marginBottom: "1.25rem",
          }}
        >
          ⚠️ {error}
        </div>
      )}

      {/* KPI Stat Cards Grid */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
          gap: "1.25rem",
          marginBottom: "1.75rem",
        }}
      >
        {/* Total Net Worth Card */}
        <div
          style={{
            background: summary.net_worth_inr >= 0 ? "rgba(16, 185, 129, 0.1)" : "rgba(239, 68, 68, 0.1)",
            border: `1.5px solid ${summary.net_worth_inr >= 0 ? "#10b981" : "#ef4444"}`,
            borderRadius: "14px",
            padding: "1.25rem",
            position: "relative",
            overflow: "hidden",
          }}
        >
          <div style={{ fontSize: "0.8rem", textTransform: "uppercase", letterSpacing: "1px", color: summary.net_worth_inr >= 0 ? "#34d399" : "#f87171", fontWeight: 700 }}>
            Total Net Worth
          </div>
          <div
            style={{
              fontSize: "1.85rem",
              fontWeight: 900,
              color: summary.net_worth_inr >= 0 ? "#34d399" : "#f87171",
              margin: "0.4rem 0 0.2rem",
            }}
          >
            {formatCurrency(summary.net_worth_inr)}
          </div>
          <div style={{ fontSize: "0.75rem", color: "#94a3b8" }}>Assets - Liabilities</div>
        </div>

        {/* Total Assets Card */}
        <div
          style={{
            background: "#1e293b",
            border: "1px solid #334155",
            borderRadius: "14px",
            padding: "1.25rem",
          }}
        >
          <div style={{ fontSize: "0.8rem", textTransform: "uppercase", color: "#38bdf8", fontWeight: 700 }}>
            Total Assets
          </div>
          <div style={{ fontSize: "1.6rem", fontWeight: 800, color: "#f8fafc", margin: "0.4rem 0 0.2rem" }}>
            {formatCurrency(summary.total_assets_inr)}
          </div>
          <div style={{ fontSize: "0.75rem", color: "#94a3b8" }}>
            Accounts: {formatCurrency(summary.total_account_assets_inr)} | Special: {formatCurrency(summary.special_investments_inr)}
          </div>
        </div>

        {/* Total Liabilities Card */}
        <div
          style={{
            background: "#1e293b",
            border: "1px solid #334155",
            borderRadius: "14px",
            padding: "1.25rem",
          }}
        >
          <div style={{ fontSize: "0.8rem", textTransform: "uppercase", color: "#f87171", fontWeight: 700 }}>
            Total Liabilities
          </div>
          <div style={{ fontSize: "1.6rem", fontWeight: 800, color: "#f87171", margin: "0.4rem 0 0.2rem" }}>
            {formatCurrency(summary.total_liabilities_inr)}
          </div>
          <div style={{ fontSize: "0.75rem", color: "#94a3b8" }}>Loans & Credit Cards</div>
        </div>

        {/* Projected Monthly Return Income */}
        <div
          style={{
            background: "#1e293b",
            border: "1px solid #334155",
            borderRadius: "14px",
            padding: "1.25rem",
          }}
        >
          <div style={{ fontSize: "0.8rem", textTransform: "uppercase", color: "#a78bfa", fontWeight: 700 }}>
            Projected Monthly Income
          </div>
          <div
            style={{
              fontSize: "1.6rem",
              fontWeight: 800,
              color: summary.projected_monthly_income_inr >= 0 ? "#a78bfa" : "#f87171",
              margin: "0.4rem 0 0.2rem",
            }}
          >
            {formatCurrency(summary.projected_monthly_income_inr)} / mo
          </div>
          <div style={{ fontSize: "0.75rem", color: "#94a3b8" }}>Net Monthly Return Yield</div>
        </div>
      </div>

      {/* Projection vs Actual Time-Series Graph */}
      <ProjectionChart />

      {/* Live 4-Asset Market Ticker */}
      <h3 style={{ margin: "0 0 1rem", fontSize: "1.1rem", fontWeight: 700, color: "#cbd5e1" }}>
        📈 Live 4-Core Investments Ticker
      </h3>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))",
          gap: "1rem",
        }}
      >
        {/* Uber */}
        <div style={{ background: "#0f172a", border: "1px solid #1e293b", borderRadius: "12px", padding: "1rem" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span style={{ fontWeight: 700, color: "#38bdf8" }}>📈 UBER</span>
            <span style={{ fontSize: "0.75rem", color: "#94a3b8" }}>{uber?.quantity || 0} Shares</span>
          </div>
          <div style={{ margin: "0.5rem 0 0.2rem", fontSize: "1.15rem", fontWeight: 800 }}>
            {formatCurrency(uber?.total_valuation_inr || 0)}
          </div>
          <div style={{ fontSize: "0.75rem", color: "#94a3b8" }}>
            Unit: ${summary.market_prices.uber_usd} USD (≈ {formatCurrency(uber?.unit_price_inr || 0)})
          </div>
        </div>

        {/* Accenture */}
        <div style={{ background: "#0f172a", border: "1px solid #1e293b", borderRadius: "12px", padding: "1rem" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span style={{ fontWeight: 700, color: "#38bdf8" }}>💻 ACN</span>
            <span style={{ fontSize: "0.75rem", color: "#94a3b8" }}>{acn?.quantity || 0} Shares</span>
          </div>
          <div style={{ margin: "0.5rem 0 0.2rem", fontSize: "1.15rem", fontWeight: 800 }}>
            {formatCurrency(acn?.total_valuation_inr || 0)}
          </div>
          <div style={{ fontSize: "0.75rem", color: "#94a3b8" }}>
            Unit: ${summary.market_prices.accenture_usd} USD (≈ {formatCurrency(acn?.unit_price_inr || 0)})
          </div>
        </div>

        {/* Gold */}
        <div style={{ background: "#0f172a", border: "1px solid #1e293b", borderRadius: "12px", padding: "1rem" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span style={{ fontWeight: 700, color: "#fbbf24" }}>🪙 Gold 24K</span>
            <span style={{ fontSize: "0.75rem", color: "#94a3b8" }}>{gold?.quantity || 0} x 10g</span>
          </div>
          <div style={{ margin: "0.5rem 0 0.2rem", fontSize: "1.15rem", fontWeight: 800, color: "#fbbf24" }}>
            {formatCurrency(gold?.total_valuation_inr || 0)}
          </div>
          <div style={{ fontSize: "0.75rem", color: "#94a3b8" }}>
            Unit: {formatCurrency(gold?.unit_price_inr || summary.market_prices.gold_10g_inr)} / 10g
          </div>
        </div>

        {/* Silver */}
        <div style={{ background: "#0f172a", border: "1px solid #1e293b", borderRadius: "12px", padding: "1rem" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span style={{ fontWeight: 700, color: "#cbd5e1" }}>🥈 Silver</span>
            <span style={{ fontSize: "0.75rem", color: "#94a3b8" }}>{silver?.quantity || 0} x 1kg</span>
          </div>
          <div style={{ margin: "0.5rem 0 0.2rem", fontSize: "1.15rem", fontWeight: 800, color: "#cbd5e1" }}>
            {formatCurrency(silver?.total_valuation_inr || 0)}
          </div>
          <div style={{ fontSize: "0.75rem", color: "#94a3b8" }}>
            Unit: {formatCurrency(silver?.unit_price_inr || summary.market_prices.silver_1kg_inr)} / 1kg
          </div>
        </div>
      </div>

      {/* Modal */}
      <NetWorthManagerModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        accounts={summary.accounts}
        specialAssets={summary.special_investments_breakdown}
        onAddAccount={handleAddAccount}
        onDeleteAccount={handleDeleteAccount}
        onUpdateSpecialAssets={handleUpdateSpecialAssets}
      />

      {/* CSS Keyframes for spin animation */}
      <style jsx global>{`
        @keyframes spin {
          from {
            transform: rotate(0deg);
          }
          to {
            transform: rotate(360deg);
          }
        }
      `}</style>
    </div>
  );
}
