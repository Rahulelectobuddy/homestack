"use client";

import React, { useState, useEffect } from "react";
import { getApiBaseUrl } from "../utils/api";

export interface ProjectionPoint {
  month_label: string;
  month_offset: number;
  is_future: boolean;
  actual_net_worth_inr?: number | null;
  projected_net_worth_inr: number;
  variance_inr?: number | null;
}

export interface ProjectionsData {
  current_net_worth_inr: number;
  projected_monthly_income_inr: number;
  points: ProjectionPoint[];
}

interface ProjectionChartProps {
  data?: ProjectionsData | null;
}

export default function ProjectionChart({ data: propData }: ProjectionChartProps) {
  const [data, setData] = useState<ProjectionsData | null>(propData || null);
  const [loading, setLoading] = useState(!propData);
  const [hoveredPoint, setHoveredPoint] = useState<ProjectionPoint | null>(null);

  useEffect(() => {
    if (!propData) {
      const fetchProjections = async () => {
        try {
          const res = await fetch(`${getApiBaseUrl()}/api/v1/net-worth/projections`);
          if (res.ok) {
            const json: ProjectionsData = await res.json();
            setData(json);
          }
        } catch (err) {
          console.error("Failed to fetch projections:", err);
        } finally {
          setLoading(false);
        }
      };
      fetchProjections();
    }
  }, [propData]);

  if (loading) {
    return (
      <div style={{ padding: "2rem", textAlign: "center", color: "#94a3b8" }}>
        ⌛ Loading projection chart...
      </div>
    );
  }

  // Fallback demonstration series if offline
  const chartData = data || {
    current_net_worth_inr: 2154000,
    projected_monthly_income_inr: 8550,
    points: [
      { month_label: "May 26", month_offset: -5, is_future: false, actual_net_worth_inr: 2092000, projected_net_worth_inr: 2111250, variance_inr: -19250 },
      { month_label: "Jun 26", month_offset: -4, is_future: false, actual_net_worth_inr: 2118000, projected_net_worth_inr: 2119800, variance_inr: -1800 },
      { month_label: "Jul 26", month_offset: -3, is_future: false, actual_net_worth_inr: 2135000, projected_net_worth_inr: 2128350, variance_inr: 6650 },
      { month_label: "Aug 26", month_offset: -2, is_future: false, actual_net_worth_inr: 2142000, projected_net_worth_inr: 2136900, variance_inr: 5100 },
      { month_label: "Sep 26", month_offset: -1, is_future: false, actual_net_worth_inr: 2149500, projected_net_worth_inr: 2145450, variance_inr: 4050 },
      { month_label: "Oct 26", month_offset: 0, is_future: false, actual_net_worth_inr: 2154000, projected_net_worth_inr: 2154000, variance_inr: 0 },
      { month_label: "Nov 26", month_offset: 1, is_future: true, actual_net_worth_inr: null, projected_net_worth_inr: 2162550, variance_inr: null },
      { month_label: "Dec 26", month_offset: 2, is_future: true, actual_net_worth_inr: null, projected_net_worth_inr: 2171100, variance_inr: null },
      { month_label: "Jan 27", month_offset: 3, is_future: true, actual_net_worth_inr: null, projected_net_worth_inr: 2179650, variance_inr: null },
      { month_label: "Feb 27", month_offset: 4, is_future: true, actual_net_worth_inr: null, projected_net_worth_inr: 2188200, variance_inr: null },
      { month_label: "Mar 27", month_offset: 5, is_future: true, actual_net_worth_inr: null, projected_net_worth_inr: 2196750, variance_inr: null },
    ],
  };

  const points = chartData.points;
  const formatCurrency = (val: number) => {
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 0,
    }).format(val);
  };

  // Compute SVG dimensions and scales
  const width = 800;
  const height = 300;
  const paddingLeft = 70;
  const paddingRight = 30;
  const paddingTop = 30;
  const paddingBottom = 40;

  const chartWidth = width - paddingLeft - paddingRight;
  const chartHeight = height - paddingTop - paddingBottom;

  const allValues: number[] = [];
  points.forEach((p) => {
    allValues.push(p.projected_net_worth_inr);
    if (p.actual_net_worth_inr != null) allValues.push(p.actual_net_worth_inr);
  });

  const minVal = Math.min(...allValues) * 0.985;
  const maxVal = Math.max(...allValues) * 1.015;

  const getX = (index: number) => {
    return paddingLeft + (index / (points.length - 1)) * chartWidth;
  };

  const getY = (val: number) => {
    return paddingTop + chartHeight - ((val - minVal) / (maxVal - minVal)) * chartHeight;
  };

  // Generate SVG path strings
  const projectedPath = points
    .map((p, i) => `${i === 0 ? "M" : "L"} ${getX(i)} ${getY(p.projected_net_worth_inr)}`)
    .join(" ");

  const actualPoints = points.filter((p) => p.actual_net_worth_inr != null);
  const actualPath = actualPoints
    .map((p, i) => {
      const origIndex = points.findIndex((pt) => pt.month_label === p.month_label);
      return `${i === 0 ? "M" : "L"} ${getX(origIndex)} ${getY(p.actual_net_worth_inr!)}`;
    })
    .join(" ");

  return (
    <div
      style={{
        background: "#0f172a",
        border: "1px solid #1e293b",
        borderRadius: "16px",
        padding: "1.5rem",
        color: "#f8fafc",
        marginBottom: "1.5rem",
      }}
    >
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: "1rem",
          marginBottom: "1rem",
        }}
      >
        <div>
          <h3 style={{ margin: 0, fontSize: "1.15rem", fontWeight: 700, color: "#38bdf8" }}>
            📊 Net Worth Trajectory: Projection vs. Actual
          </h3>
          <p style={{ margin: "4px 0 0", fontSize: "0.825rem", color: "#94a3b8" }}>
            Monthly Expected Yield Target: +{formatCurrency(chartData.projected_monthly_income_inr)} / mo
          </p>
        </div>

        {/* Legend */}
        <div style={{ display: "flex", gap: "1.25rem", fontSize: "0.85rem", fontWeight: 600 }}>
          <div style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}>
            <span style={{ width: "12px", height: "12px", borderRadius: "50%", background: "#10b981", display: "inline-block" }}></span>
            <span style={{ color: "#34d399" }}>Actual Net Worth</span>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}>
            <span style={{ width: "14px", height: "3px", background: "#38bdf8", display: "inline-block" }}></span>
            <span style={{ color: "#38bdf8" }}>Projected Target</span>
          </div>
        </div>
      </div>

      {/* SVG Line Chart */}
      <div style={{ width: "100%", overflowX: "auto" }}>
        <svg viewBox={`0 0 ${width} ${height}`} style={{ width: "100%", height: "auto", minWidth: "600px" }}>
          {/* Horizontal Grid lines & Y Axis Labels */}
          {[0, 0.25, 0.5, 0.75, 1].map((pct, idx) => {
            const val = minVal + pct * (maxVal - minVal);
            const yPos = paddingTop + chartHeight - pct * chartHeight;
            return (
              <g key={idx}>
                <line x1={paddingLeft} y1={yPos} x2={width - paddingRight} y2={yPos} stroke="#1e293b" strokeDasharray="4 4" />
                <text x={paddingLeft - 8} y={yPos + 4} fill="#64748b" fontSize="10" textAnchor="end">
                  ₹{(val / 100000).toFixed(1)}L
                </text>
              </g>
            );
          })}

          {/* X Axis Labels */}
          {points.map((p, i) => (
            <text
              key={i}
              x={getX(i)}
              y={height - 12}
              fill={p.is_future ? "#64748b" : "#94a3b8"}
              fontSize="11"
              fontWeight={p.month_offset === 0 ? "bold" : "normal"}
              textAnchor="middle"
            >
              {p.month_label}
            </text>
          ))}

          {/* Projected Path Line (Dashed) */}
          <path d={projectedPath} fill="none" stroke="#38bdf8" strokeWidth="2.5" strokeDasharray="6 4" opacity="0.85" />

          {/* Actual Path Line (Solid) */}
          {actualPath && <path d={actualPath} fill="none" stroke="#10b981" strokeWidth="3" />}

          {/* Data Points / Dots */}
          {points.map((p, i) => {
            const x = getX(i);
            const projY = getY(p.projected_net_worth_inr);
            const isHovered = hoveredPoint?.month_label === p.month_label;

            return (
              <g key={i} onMouseEnter={() => setHoveredPoint(p)} onMouseLeave={() => setHoveredPoint(null)} style={{ cursor: "pointer" }}>
                {/* Projected Dot */}
                <circle cx={x} cy={projY} r={isHovered ? 6 : 4} fill="#0f172a" stroke="#38bdf8" strokeWidth="2" />

                {/* Actual Dot */}
                {p.actual_net_worth_inr != null && (
                  <circle cx={x} cy={getY(p.actual_net_worth_inr)} r={isHovered ? 7 : 5} fill="#10b981" stroke="#ffffff" strokeWidth="2" />
                )}
              </g>
            );
          })}
        </svg>
      </div>

      {/* Hover Info Tooltip Banner */}
      <div
        style={{
          marginTop: "0.75rem",
          padding: "0.75rem 1rem",
          background: "#1e293b",
          borderRadius: "8px",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          fontSize: "0.875rem",
        }}
      >
        {hoveredPoint ? (
          <>
            <div>
              <span style={{ fontWeight: 700, color: "#f8fafc" }}>{hoveredPoint.month_label}: </span>
              <span style={{ color: "#38bdf8" }}>Projected: {formatCurrency(hoveredPoint.projected_net_worth_inr)}</span>
              {hoveredPoint.actual_net_worth_inr != null && (
                <span style={{ color: "#34d399", marginLeft: "1rem" }}>
                  Actual: {formatCurrency(hoveredPoint.actual_net_worth_inr)}
                </span>
              )}
            </div>
            {hoveredPoint.variance_inr != null && (
              <div
                style={{
                  fontWeight: 700,
                  color: hoveredPoint.variance_inr >= 0 ? "#34d399" : "#f87171",
                }}
              >
                Variance: {hoveredPoint.variance_inr >= 0 ? "+" : ""}
                {formatCurrency(hoveredPoint.variance_inr)}
              </div>
            )}
          </>
        ) : (
          <div style={{ color: "#94a3b8", fontStyle: "italic" }}>
            💡 Hover over any month data point to inspect actual vs. projected valuation variance.
          </div>
        )}
      </div>
    </div>
  );
}
