"use client";

import React, { useState } from "react";

export interface AccountBalance {
  id: number;
  account_name: string;
  account_type: "asset" | "liability";
  balance_inr: number;
  monthly_return_pct: number;
}

export interface SpecialAssetHolding {
  id: number;
  asset_key: string;
  asset_name: string;
  quantity: number;
  unit_price_usd?: number | null;
  unit_price_inr: number;
  total_valuation_inr: number;
  manual_price_override_inr?: number | null;
}

interface NetWorthManagerModalProps {
  isOpen: boolean;
  onClose: () => void;
  accounts: AccountBalance[];
  specialAssets: SpecialAssetHolding[];
  onAddAccount: (acc: { account_name: string; account_type: "asset" | "liability"; balance_inr: number; monthly_return_pct: number }) => Promise<void>;
  onDeleteAccount: (id: number) => Promise<void>;
  onUpdateSpecialAssets: (holdings: { uber_stock: number; accenture_stock: number; gold_10g: number; silver_1kg: number }) => Promise<void>;
}

export default function NetWorthManagerModal({
  isOpen,
  onClose,
  accounts,
  specialAssets,
  onAddAccount,
  onDeleteAccount,
  onUpdateSpecialAssets,
}: NetWorthManagerModalProps) {
  const [activeTab, setActiveTab] = useState<"accounts" | "assets">("accounts");

  // Account form state
  const [accName, setAccName] = useState("");
  const [accType, setAccType] = useState<"asset" | "liability">("asset");
  const [accBalance, setAccBalance] = useState("");
  const [accReturnPct, setAccReturnPct] = useState("");
  const [isSubmittingAccount, setIsSubmittingAccount] = useState(false);

  // Asset holdings form state
  const uberHolding = specialAssets.find((a) => a.asset_key === "uber_stock");
  const acnHolding = specialAssets.find((a) => a.asset_key === "accenture_stock");
  const goldHolding = specialAssets.find((a) => a.asset_key === "gold_10g");
  const silverHolding = specialAssets.find((a) => a.asset_key === "silver_1kg");

  const [uberQty, setUberQty] = useState(uberHolding ? uberHolding.quantity.toString() : "0");
  const [acnQty, setAcnQty] = useState(acnHolding ? acnHolding.quantity.toString() : "0");
  const [goldQty, setGoldQty] = useState(goldHolding ? goldHolding.quantity.toString() : "0");
  const [silverQty, setSilverQty] = useState(silverHolding ? silverHolding.quantity.toString() : "0");
  const [isSubmittingAssets, setIsSubmittingAssets] = useState(false);

  if (!isOpen) return null;

  const handleCreateAccountSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!accName.trim()) return;

    setIsSubmittingAccount(true);
    try {
      await onAddAccount({
        account_name: accName.trim(),
        account_type: accType,
        balance_inr: parseFloat(accBalance) || 0,
        monthly_return_pct: parseFloat(accReturnPct) || 0,
      });
      setAccName("");
      setAccBalance("");
      setAccReturnPct("");
    } catch (err) {
      console.error("Error creating account:", err);
    } finally {
      setIsSubmittingAccount(false);
    }
  };

  const handleUpdateAssetsSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmittingAssets(true);
    try {
      await onUpdateSpecialAssets({
        uber_stock: parseFloat(uberQty) || 0,
        accenture_stock: parseFloat(acnQty) || 0,
        gold_10g: parseFloat(goldQty) || 0,
        silver_1kg: parseFloat(silverQty) || 0,
      });
    } catch (err) {
      console.error("Error updating special assets:", err);
    } finally {
      setIsSubmittingAssets(false);
    }
  };

  const formatCurrency = (val: number) => {
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 2,
    }).format(val);
  };

  return (
    <div
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: "rgba(15, 23, 42, 0.75)",
        backdropFilter: "blur(6px)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 1000,
        padding: "1rem",
      }}
    >
      <div
        style={{
          background: "#0f172a",
          border: "1px solid #334155",
          borderRadius: "16px",
          width: "100%",
          maxWidth: "750px",
          maxHeight: "90vh",
          display: "flex",
          flexDirection: "column",
          boxShadow: "0 25px 50px -12px rgba(0, 0, 0, 0.5)",
          color: "#f8fafc",
          overflow: "hidden",
        }}
      >
        {/* Header */}
        <div
          style={{
            padding: "1.25rem 1.5rem",
            borderBottom: "1px solid #1e293b",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
          }}
        >
          <div>
            <h2 style={{ margin: 0, fontSize: "1.25rem", fontWeight: 700, color: "#f8fafc" }}>
              ⚙️ Financial Engine & Asset Manager
            </h2>
            <p style={{ margin: "4px 0 0", fontSize: "0.85rem", color: "#94a3b8" }}>
              Configure bank accounts, loan liabilities, and 4 core investment quantities
            </p>
          </div>
          <button
            onClick={onClose}
            style={{
              background: "transparent",
              border: "none",
              color: "#94a3b8",
              fontSize: "1.5rem",
              cursor: "pointer",
              padding: "0.25rem 0.5rem",
              borderRadius: "6px",
            }}
          >
            ✕
          </button>
        </div>

        {/* Tab Navigation */}
        <div
          style={{
            display: "flex",
            borderBottom: "1px solid #1e293b",
            background: "#1e293b",
            padding: "0 1.5rem",
          }}
        >
          <button
            onClick={() => setActiveTab("accounts")}
            style={{
              padding: "0.85rem 1.25rem",
              background: "transparent",
              border: "none",
              borderBottom: activeTab === "accounts" ? "3px solid #38bdf8" : "3px solid transparent",
              color: activeTab === "accounts" ? "#38bdf8" : "#94a3b8",
              fontWeight: 600,
              cursor: "pointer",
              fontSize: "0.95rem",
            }}
          >
            🏦 Accounts & Loans ({accounts.length})
          </button>
          <button
            onClick={() => setActiveTab("assets")}
            style={{
              padding: "0.85rem 1.25rem",
              background: "transparent",
              border: "none",
              borderBottom: activeTab === "assets" ? "3px solid #38bdf8" : "3px solid transparent",
              color: activeTab === "assets" ? "#38bdf8" : "#94a3b8",
              fontWeight: 600,
              cursor: "pointer",
              fontSize: "0.95rem",
            }}
          >
            📈 4 Special Investments
          </button>
        </div>

        {/* Body Content */}
        <div style={{ padding: "1.5rem", overflowY: "auto", flex: 1 }}>
          {activeTab === "accounts" && (
            <div>
              {/* Add Account Form */}
              <form
                onSubmit={handleCreateAccountSubmit}
                style={{
                  background: "#1e293b",
                  padding: "1.25rem",
                  borderRadius: "12px",
                  border: "1px solid #334155",
                  marginBottom: "1.5rem",
                }}
              >
                <h4 style={{ margin: "0 0 1rem", color: "#f8fafc", fontSize: "1rem" }}>
                  + Add New Bank Account or Loan Liability
                </h4>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem" }}>
                  <div>
                    <label style={{ display: "block", fontSize: "0.8rem", color: "#94a3b8", marginBottom: "4px" }}>
                      Account / Loan Name
                    </label>
                    <input
                      type="text"
                      placeholder="e.g. HDFC Salary, SBI Home Loan"
                      value={accName}
                      onChange={(e) => setAccName(e.target.value)}
                      required
                      style={{
                        width: "100%",
                        padding: "0.6rem 0.75rem",
                        borderRadius: "6px",
                        border: "1px solid #475569",
                        background: "#0f172a",
                        color: "#f8fafc",
                        fontSize: "0.9rem",
                      }}
                    />
                  </div>

                  <div>
                    <label style={{ display: "block", fontSize: "0.8rem", color: "#94a3b8", marginBottom: "4px" }}>
                      Classification Type
                    </label>
                    <select
                      value={accType}
                      onChange={(e) => setAccType(e.target.value as "asset" | "liability")}
                      style={{
                        width: "100%",
                        padding: "0.6rem 0.75rem",
                        borderRadius: "6px",
                        border: "1px solid #475569",
                        background: "#0f172a",
                        color: "#f8fafc",
                        fontSize: "0.9rem",
                      }}
                    >
                      <option value="asset">Asset (Savings, FD, Mutual Fund)</option>
                      <option value="liability">Liability (Home Loan, Credit Card)</option>
                    </select>
                  </div>

                  <div>
                    <label style={{ display: "block", fontSize: "0.8rem", color: "#94a3b8", marginBottom: "4px" }}>
                      Current Balance (₹ INR)
                    </label>
                    <input
                      type="number"
                      step="any"
                      placeholder="e.g. 250000"
                      value={accBalance}
                      onChange={(e) => setAccBalance(e.target.value)}
                      required
                      style={{
                        width: "100%",
                        padding: "0.6rem 0.75rem",
                        borderRadius: "6px",
                        border: "1px solid #475569",
                        background: "#0f172a",
                        color: "#f8fafc",
                        fontSize: "0.9rem",
                      }}
                    />
                  </div>

                  <div>
                    <label style={{ display: "block", fontSize: "0.8rem", color: "#94a3b8", marginBottom: "4px" }}>
                      Expected Monthly Return (%)
                    </label>
                    <input
                      type="number"
                      step="any"
                      placeholder="e.g. 0.5 (+0.5%/mo) or 0.75"
                      value={accReturnPct}
                      onChange={(e) => setAccReturnPct(e.target.value)}
                      style={{
                        width: "100%",
                        padding: "0.6rem 0.75rem",
                        borderRadius: "6px",
                        border: "1px solid #475569",
                        background: "#0f172a",
                        color: "#f8fafc",
                        fontSize: "0.9rem",
                      }}
                    />
                  </div>
                </div>

                <div style={{ marginTop: "1rem", textAlign: "right" }}>
                  <button
                    type="submit"
                    disabled={isSubmittingAccount}
                    style={{
                      background: "#2563eb",
                      color: "#ffffff",
                      border: "none",
                      padding: "0.6rem 1.25rem",
                      borderRadius: "6px",
                      fontWeight: 600,
                      cursor: "pointer",
                      fontSize: "0.9rem",
                    }}
                  >
                    {isSubmittingAccount ? "Saving..." : "+ Add Account"}
                  </button>
                </div>
              </form>

              {/* Accounts Table */}
              <h4 style={{ margin: "0 0 0.75rem", color: "#cbd5e1" }}>Current Accounts & Liabilities</h4>
              {accounts.length === 0 ? (
                <p style={{ color: "#64748b", fontStyle: "italic" }}>No bank accounts or loans added yet.</p>
              ) : (
                <div style={{ overflowX: "auto" }}>
                  <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.9rem" }}>
                    <thead>
                      <tr style={{ background: "#1e293b", color: "#94a3b8", textAlign: "left" }}>
                        <th style={{ padding: "0.75rem" }}>Name</th>
                        <th style={{ padding: "0.75rem" }}>Type</th>
                        <th style={{ padding: "0.75rem" }}>Balance (₹)</th>
                        <th style={{ padding: "0.75rem" }}>Monthly Return</th>
                        <th style={{ padding: "0.75rem", textAlign: "center" }}>Action</th>
                      </tr>
                    </thead>
                    <tbody>
                      {accounts.map((acc) => (
                        <tr key={acc.id} style={{ borderBottom: "1px solid #1e293b" }}>
                          <td style={{ padding: "0.75rem", fontWeight: 600 }}>{acc.account_name}</td>
                          <td style={{ padding: "0.75rem" }}>
                            <span
                              style={{
                                padding: "0.2rem 0.5rem",
                                borderRadius: "4px",
                                fontSize: "0.75rem",
                                fontWeight: 700,
                                textTransform: "uppercase",
                                background: acc.account_type === "asset" ? "rgba(16, 185, 129, 0.15)" : "rgba(239, 68, 68, 0.15)",
                                color: acc.account_type === "asset" ? "#34d399" : "#f87171",
                                border: `1px solid ${acc.account_type === "asset" ? "#059669" : "#dc2626"}`,
                              }}
                            >
                              {acc.account_type}
                            </span>
                          </td>
                          <td style={{ padding: "0.75rem", fontWeight: 600, color: acc.account_type === "asset" ? "#34d399" : "#f87171" }}>
                            {formatCurrency(acc.balance_inr)}
                          </td>
                          <td style={{ padding: "0.75rem", color: "#94a3b8" }}>{acc.monthly_return_pct}% / mo</td>
                          <td style={{ padding: "0.75rem", textAlign: "center" }}>
                            <button
                              onClick={() => onDeleteAccount(acc.id)}
                              style={{
                                background: "#ef4444",
                                color: "#fff",
                                border: "none",
                                padding: "0.3rem 0.6rem",
                                borderRadius: "4px",
                                cursor: "pointer",
                                fontSize: "0.8rem",
                              }}
                            >
                              🗑️ Delete
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {activeTab === "assets" && (
            <form onSubmit={handleUpdateAssetsSubmit}>
              <p style={{ color: "#94a3b8", fontSize: "0.9rem", marginBottom: "1.25rem" }}>
                Update quantities for your 4 special investment assets. Real-time market prices & FX rates will automatically calculate total valuations.
              </p>

              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1.25rem" }}>
                <div style={{ background: "#1e293b", padding: "1.25rem", borderRadius: "12px", border: "1px solid #334155" }}>
                  <h4 style={{ margin: "0 0 0.5rem", color: "#38bdf8" }}>📈 Uber Technologies (UBER)</h4>
                  <label style={{ display: "block", fontSize: "0.8rem", color: "#94a3b8", marginBottom: "4px" }}>
                    Quantity (Shares)
                  </label>
                  <input
                    type="number"
                    step="any"
                    value={uberQty}
                    onChange={(e) => setUberQty(e.target.value)}
                    style={{
                      width: "100%",
                      padding: "0.6rem 0.75rem",
                      borderRadius: "6px",
                      border: "1px solid #475569",
                      background: "#0f172a",
                      color: "#f8fafc",
                      fontSize: "0.95rem",
                      fontWeight: 600,
                    }}
                  />
                  {uberHolding && (
                    <p style={{ margin: "8px 0 0", fontSize: "0.8rem", color: "#94a3b8" }}>
                      Current Unit Price: ${uberHolding.unit_price_usd?.toFixed(2) || "-"} (≈ {formatCurrency(uberHolding.unit_price_inr)})
                    </p>
                  )}
                </div>

                <div style={{ background: "#1e293b", padding: "1.25rem", borderRadius: "12px", border: "1px solid #334155" }}>
                  <h4 style={{ margin: "0 0 0.5rem", color: "#38bdf8" }}>💻 Accenture plc (ACN)</h4>
                  <label style={{ display: "block", fontSize: "0.8rem", color: "#94a3b8", marginBottom: "4px" }}>
                    Quantity (Shares)
                  </label>
                  <input
                    type="number"
                    step="any"
                    value={acnQty}
                    onChange={(e) => setAcnQty(e.target.value)}
                    style={{
                      width: "100%",
                      padding: "0.6rem 0.75rem",
                      borderRadius: "6px",
                      border: "1px solid #475569",
                      background: "#0f172a",
                      color: "#f8fafc",
                      fontSize: "0.95rem",
                      fontWeight: 600,
                    }}
                  />
                  {acnHolding && (
                    <p style={{ margin: "8px 0 0", fontSize: "0.8rem", color: "#94a3b8" }}>
                      Current Unit Price: ${acnHolding.unit_price_usd?.toFixed(2) || "-"} (≈ {formatCurrency(acnHolding.unit_price_inr)})
                    </p>
                  )}
                </div>

                <div style={{ background: "#1e293b", padding: "1.25rem", borderRadius: "12px", border: "1px solid #334155" }}>
                  <h4 style={{ margin: "0 0 0.5rem", color: "#fbbf24" }}>🪙 Gold 24K (10-Gram units)</h4>
                  <label style={{ display: "block", fontSize: "0.8rem", color: "#94a3b8", marginBottom: "4px" }}>
                    Quantity (10g Units)
                  </label>
                  <input
                    type="number"
                    step="any"
                    value={goldQty}
                    onChange={(e) => setGoldQty(e.target.value)}
                    style={{
                      width: "100%",
                      padding: "0.6rem 0.75rem",
                      borderRadius: "6px",
                      border: "1px solid #475569",
                      background: "#0f172a",
                      color: "#f8fafc",
                      fontSize: "0.95rem",
                      fontWeight: 600,
                    }}
                  />
                  {goldHolding && (
                    <p style={{ margin: "8px 0 0", fontSize: "0.8rem", color: "#94a3b8" }}>
                      Current Unit Price: {formatCurrency(goldHolding.unit_price_inr)} / 10g
                    </p>
                  )}
                </div>

                <div style={{ background: "#1e293b", padding: "1.25rem", borderRadius: "12px", border: "1px solid #334155" }}>
                  <h4 style={{ margin: "0 0 0.5rem", color: "#cbd5e1" }}>🥈 Silver (1-Kg units)</h4>
                  <label style={{ display: "block", fontSize: "0.8rem", color: "#94a3b8", marginBottom: "4px" }}>
                    Quantity (1kg Units)
                  </label>
                  <input
                    type="number"
                    step="any"
                    value={silverQty}
                    onChange={(e) => setSilverQty(e.target.value)}
                    style={{
                      width: "100%",
                      padding: "0.6rem 0.75rem",
                      borderRadius: "6px",
                      border: "1px solid #475569",
                      background: "#0f172a",
                      color: "#f8fafc",
                      fontSize: "0.95rem",
                      fontWeight: 600,
                    }}
                  />
                  {silverHolding && (
                    <p style={{ margin: "8px 0 0", fontSize: "0.8rem", color: "#94a3b8" }}>
                      Current Unit Price: {formatCurrency(silverHolding.unit_price_inr)} / 1kg
                    </p>
                  )}
                </div>
              </div>

              <div style={{ marginTop: "1.5rem", textAlign: "right" }}>
                <button
                  type="submit"
                  disabled={isSubmittingAssets}
                  style={{
                    background: "#10b981",
                    color: "#ffffff",
                    border: "none",
                    padding: "0.75rem 1.5rem",
                    borderRadius: "8px",
                    fontWeight: 700,
                    cursor: "pointer",
                    fontSize: "0.95rem",
                  }}
                >
                  {isSubmittingAssets ? "Saving Assets..." : "💾 Save Asset Quantities"}
                </button>
              </div>
            </form>
          )}
        </div>

        {/* Footer */}
        <div
          style={{
            padding: "1rem 1.5rem",
            borderTop: "1px solid #1e293b",
            background: "#0f172a",
            textAlign: "right",
          }}
        >
          <button
            onClick={onClose}
            style={{
              background: "#334155",
              color: "#f8fafc",
              border: "none",
              padding: "0.5rem 1.25rem",
              borderRadius: "6px",
              cursor: "pointer",
              fontWeight: 600,
            }}
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
