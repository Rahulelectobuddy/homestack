"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";

interface BusRecord {
  id: number;
  scraped_at: string;
  scrape_date: string;
  travel_date: string;
  days_until_travel: number;
  operator_name: string;
  bus_type: string;
  seat_type: string;
  price: number;
  available_seats: number;
  has_toilet: boolean;
}

interface SeatBreakdown {
  seat_type: string;
  min_price: number;
  max_price: number;
  avg_price: number;
  total_buses: number;
}

interface FareTrend {
  travel_date: string;
  min_price: number;
  avg_price: number;
}

interface AnalyticsData {
  status: string;
  route: string;
  total_records: number;
  summary: {
    min_fare: number;
    max_fare: number;
    avg_fare: number;
  };
  seat_type_breakdown: SeatBreakdown[];
  fare_trends: FareTrend[];
  records: BusRecord[];
}

interface TrendPoint {
  id: number;
  scraped_at: string;
  scrape_time_label: string;
  travel_date: string;
  operator_name: string;
  seat_type: string;
  price: number;
  available_seats: number;
}

interface TrendResponse {
  status: string;
  available_operators: string[];
  available_travel_dates: string[];
  available_seat_types: string[];
  series: TrendPoint[];
}

export default function BusFaresAnalyticsPage() {
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedSeatType, setSelectedSeatType] = useState<string>("all");
  const [searchOperator, setSearchOperator] = useState<string>("");

  // Line Chart Filters state
  const [availableOperators, setAvailableOperators] = useState<string[]>([]);
  const [availableDates, setAvailableDates] = useState<string[]>([]);
  const [selectedOp, setSelectedOp] = useState<string>("all");
  const [selectedDate, setSelectedDate] = useState<string>("all");
  const [selectedSeat, setSelectedSeat] = useState<string>("all");
  const [trendSeries, setTrendSeries] = useState<TrendPoint[]>([]);
  const [trendLoading, setTrendLoading] = useState(false);
  const [hoveredPoint, setHoveredPoint] = useState<TrendPoint | null>(null);

  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://192.168.1.29:8000";

  useEffect(() => {
    fetchData();
  }, [selectedSeatType]);

  useEffect(() => {
    fetchTrendData();
  }, [selectedOp, selectedDate, selectedSeat]);

  const fetchData = async () => {
    setLoading(true);
    try {
      let url = `${API_URL}/api/v1/analytics/bus-fares`;
      if (selectedSeatType !== "all") {
        url += `?seat_type=${selectedSeatType}`;
      }
      const res = await fetch(url);
      const json = await res.json();
      setData(json);
    } catch (err) {
      console.error("Failed to fetch bus fares analytics:", err);
    } finally {
      setLoading(false);
    }
  };

  const fetchTrendData = async () => {
    setTrendLoading(true);
    try {
      const params = new URLSearchParams();
      if (selectedOp !== "all") params.append("operator_name", selectedOp);
      if (selectedDate !== "all") params.append("travel_date", selectedDate);
      if (selectedSeat !== "all") params.append("seat_type", selectedSeat);

      const res = await fetch(`${API_URL}/api/v1/analytics/bus-fares/trend?${params.toString()}`);
      const json: TrendResponse = await res.json();

      if (json.available_operators && json.available_operators.length > 0) {
        setAvailableOperators(json.available_operators);
      }
      if (json.available_travel_dates && json.available_travel_dates.length > 0) {
        setAvailableDates(json.available_travel_dates);
      }
      setTrendSeries(json.series || []);
    } catch (err) {
      console.error("Failed to fetch bus fare trend:", err);
    } finally {
      setTrendLoading(false);
    }
  };

  const filteredRecords = data?.records.filter((r) =>
    r.operator_name.toLowerCase().includes(searchOperator.toLowerCase())
  ) || [];

  // Line Chart Geometry Computations
  const svgWidth = 840;
  const svgHeight = 280;
  const paddingX = 60;
  const paddingY = 40;

  const prices = trendSeries.map((s) => s.price);
  const minPrice = prices.length > 0 ? Math.min(...prices) * 0.95 : 500;
  const maxPrice = prices.length > 0 ? Math.max(...prices) * 1.05 : 1500;
  const priceRange = maxPrice - minPrice || 1;

  const chartPoints = trendSeries.map((s, idx) => {
    const x = paddingX + (idx / Math.max(1, trendSeries.length - 1)) * (svgWidth - paddingX * 2);
    const y = svgHeight - paddingY - ((s.price - minPrice) / priceRange) * (svgHeight - paddingY * 2);
    return { x, y, ...s };
  });

  const pathD = chartPoints.reduce((acc, p, idx) => `${acc} ${idx === 0 ? "M" : "L"} ${p.x} ${p.y}`, "");
  const areaD = chartPoints.length > 0
    ? `${pathD} L ${chartPoints[chartPoints.length - 1].x} ${svgHeight - paddingY} L ${chartPoints[0].x} ${svgHeight - paddingY} Z`
    : "";

  return (
    <main style={{ minHeight: "100vh", background: "#0f172a", color: "#f8fafc", padding: "2rem" }}>
      <div style={{ maxWidth: "1280px", margin: "0 auto" }}>
        
        {/* Navigation & Header */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "2rem" }}>
          <div>
            <Link href="/" style={{ color: "#38bdf8", textDecoration: "none", fontSize: "0.875rem" }}>
              ← Back to Overview
            </Link>
            <h1 style={{ color: "#f8fafc", margin: "0.5rem 0 0 0", fontSize: "2rem" }}>
              🚌 Bus Fare Analytics & Trends
            </h1>
            <p style={{ color: "#94a3b8", margin: "0.25rem 0 0 0" }}>
              Pune ➔ Indore Route | Scraped every 3 hours
            </p>
          </div>
          <button
            onClick={() => { fetchData(); fetchTrendData(); }}
            style={{
              background: "#0284c7",
              color: "#fff",
              border: "none",
              padding: "0.6rem 1.2rem",
              borderRadius: "6px",
              cursor: "pointer",
              fontWeight: 600
            }}
          >
            🔄 Refresh Data
          </button>
        </div>

        {/* --- Interactive Line Chart Section --- */}
        <div style={{ background: "#1e293b", padding: "1.5rem", borderRadius: "12px", border: "1px solid #334155", marginBottom: "2.5rem" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "1rem", marginBottom: "1.5rem" }}>
            <div>
              <h2 style={{ margin: 0, color: "#38bdf8", fontSize: "1.35rem" }}>
                📈 Historical Fare Trend Analysis
              </h2>
              <p style={{ margin: "0.25rem 0 0 0", color: "#94a3b8", fontSize: "0.875rem" }}>
                Select Bus Operator, Date of Travel, and Seat Category to view fare fluctuations over scrape time.
              </p>
            </div>
            
            {/* Chart Dropdown Controls */}
            <div style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap" }}>
              {/* Operator Selector */}
              <div>
                <label style={{ display: "block", color: "#94a3b8", fontSize: "0.75rem", marginBottom: "0.2rem" }}>
                  Bus Operator
                </label>
                <select
                  value={selectedOp}
                  onChange={(e) => setSelectedOp(e.target.value)}
                  style={{
                    background: "#0f172a",
                    color: "#f8fafc",
                    border: "1px solid #334155",
                    padding: "0.45rem 0.85rem",
                    borderRadius: "6px",
                    fontSize: "0.875rem"
                  }}
                >
                  <option value="all">All Operators</option>
                  {availableOperators.map((op) => (
                    <option key={op} value={op}>{op}</option>
                  ))}
                </select>
              </div>

              {/* Date of Travel Selector */}
              <div>
                <label style={{ display: "block", color: "#94a3b8", fontSize: "0.75rem", marginBottom: "0.2rem" }}>
                  Date of Travel
                </label>
                <select
                  value={selectedDate}
                  onChange={(e) => setSelectedDate(e.target.value)}
                  style={{
                    background: "#0f172a",
                    color: "#f8fafc",
                    border: "1px solid #334155",
                    padding: "0.45rem 0.85rem",
                    borderRadius: "6px",
                    fontSize: "0.875rem"
                  }}
                >
                  <option value="all">All Travel Dates</option>
                  {availableDates.map((dt) => (
                    <option key={dt} value={dt}>{dt}</option>
                  ))}
                </select>
              </div>

              {/* Seat Type Selector */}
              <div>
                <label style={{ display: "block", color: "#94a3b8", fontSize: "0.75rem", marginBottom: "0.2rem" }}>
                  Seat Type
                </label>
                <select
                  value={selectedSeat}
                  onChange={(e) => setSelectedSeat(e.target.value)}
                  style={{
                    background: "#0f172a",
                    color: "#f8fafc",
                    border: "1px solid #334155",
                    padding: "0.45rem 0.85rem",
                    borderRadius: "6px",
                    fontSize: "0.875rem"
                  }}
                >
                  <option value="all">All Seat Types</option>
                  <option value="single_lower">Single Lower Sleeper</option>
                  <option value="single_upper">Single Upper Sleeper</option>
                  <option value="double_lower">Double Lower Sleeper</option>
                  <option value="double_upper">Double Upper Sleeper</option>
                </select>
              </div>
            </div>
          </div>

          {/* SVG Line Graph Container */}
          {trendLoading ? (
            <div style={{ height: "280px", display: "flex", alignItems: "center", justifyContent: "center", color: "#94a3b8" }}>
              Loading line chart data...
            </div>
          ) : trendSeries.length === 0 ? (
            <div style={{ height: "280px", display: "flex", alignItems: "center", justifyContent: "center", color: "#64748b" }}>
              No scrape records matching the selected operator, travel date, and seat type.
            </div>
          ) : (
            <div style={{ position: "relative", width: "100%", overflowX: "auto" }}>
              <svg viewBox={`0 0 ${svgWidth} ${svgHeight}`} style={{ width: "100%", height: "auto", display: "block" }}>
                <defs>
                  <linearGradient id="areaGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#38bdf8" stopOpacity="0.4" />
                    <stop offset="100%" stopColor="#38bdf8" stopOpacity="0.0" />
                  </linearGradient>
                </defs>

                {/* Y-Axis Gridlines & Reference Price Labels */}
                {[0, 0.33, 0.66, 1].map((ratio) => {
                  const yVal = svgHeight - paddingY - ratio * (svgHeight - paddingY * 2);
                  const priceVal = Math.round(minPrice + ratio * priceRange);
                  return (
                    <g key={ratio}>
                      <line x1={paddingX} y1={yVal} x2={svgWidth - paddingX} y2={yVal} stroke="#334155" strokeDasharray="4 4" />
                      <text x={paddingX - 10} y={yVal + 4} fill="#64748b" fontSize="11" textAnchor="end">
                        ₹{priceVal}
                      </text>
                    </g>
                  );
                })}

                {/* Gradient Area under line */}
                <path d={areaD} fill="url(#areaGradient)" />

                {/* Polyline Graph Path */}
                <path d={pathD} fill="none" stroke="#38bdf8" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />

                {/* Data Points */}
                {chartPoints.map((p, i) => (
                  <g key={i}>
                    <circle
                      cx={p.x}
                      cy={p.y}
                      r={hoveredPoint?.id === p.id ? "7" : "5"}
                      fill={hoveredPoint?.id === p.id ? "#34d399" : "#0284c7"}
                      stroke="#f8fafc"
                      strokeWidth="2"
                      style={{ cursor: "pointer", transition: "all 0.2s" }}
                      onMouseEnter={() => setHoveredPoint(p)}
                      onMouseLeave={() => setHoveredPoint(null)}
                    />
                    {/* X-Axis Date & Time of Scrape Labels */}
                    <text
                      x={p.x}
                      y={svgHeight - 12}
                      fill="#94a3b8"
                      fontSize="10"
                      textAnchor="middle"
                    >
                      {p.scrape_time_label}
                    </text>
                  </g>
                ))}
              </svg>

              {/* Axis Titles */}
              <div style={{ display: "flex", justifyContent: "space-between", color: "#64748b", fontSize: "0.75rem", marginTop: "0.5rem" }}>
                <span>⬅ Earlier Scrapes</span>
                <span style={{ fontWeight: 600, color: "#94a3b8" }}>X-Axis: Scrape Date & Time | Y-Axis: Fare (₹)</span>
                <span>Latest Scrapes ➔</span>
              </div>

              {/* Hover Tooltip Overlay */}
              {hoveredPoint && (
                <div
                  style={{
                    position: "absolute",
                    top: "10px",
                    right: "20px",
                    background: "#0f172a",
                    border: "1px solid #38bdf8",
                    borderRadius: "8px",
                    padding: "0.75rem 1rem",
                    boxShadow: "0 10px 25px rgba(0,0,0,0.5)",
                    fontSize: "0.85rem",
                    zIndex: 10
                  }}
                >
                  <div style={{ color: "#38bdf8", fontWeight: "bold" }}>{hoveredPoint.operator_name}</div>
                  <div style={{ color: "#34d399", fontSize: "1.1rem", fontWeight: "bold", margin: "0.25rem 0" }}>
                    Fare: ₹{hoveredPoint.price}
                  </div>
                  <div style={{ color: "#cbd5e1" }}>Scrape Time: {hoveredPoint.scrape_time_label}</div>
                  <div style={{ color: "#94a3b8" }}>Travel Date: {hoveredPoint.travel_date}</div>
                  <div style={{ color: "#94a3b8", textTransform: "capitalize" }}>
                    Seat: {hoveredPoint.seat_type.replace("_", " ")} ({hoveredPoint.available_seats} left)
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {loading ? (
          <div style={{ textAlign: "center", padding: "4rem", color: "#94a3b8" }}>
            Loading Bus Fares Analytics...
          </div>
        ) : (
          <>
            {/* KPI Summary Cards */}
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: "1.25rem", marginBottom: "2rem" }}>
              <div style={{ background: "#1e293b", padding: "1.25rem", borderRadius: "10px", border: "1px solid #334155" }}>
                <div style={{ color: "#94a3b8", fontSize: "0.875rem", marginBottom: "0.25rem" }}>Lowest Min Fare</div>
                <div style={{ fontSize: "2rem", fontWeight: "bold", color: "#34d399" }}>
                  ₹{data?.summary.min_fare || 0}
                </div>
                <div style={{ color: "#64748b", fontSize: "0.75rem", marginTop: "0.25rem" }}>Pune ➔ Indore</div>
              </div>

              <div style={{ background: "#1e293b", padding: "1.25rem", borderRadius: "10px", border: "1px solid #334155" }}>
                <div style={{ color: "#94a3b8", fontSize: "0.875rem", marginBottom: "0.25rem" }}>Average Fare</div>
                <div style={{ fontSize: "2rem", fontWeight: "bold", color: "#38bdf8" }}>
                  ₹{data?.summary.avg_fare || 0}
                </div>
                <div style={{ color: "#64748b", fontSize: "0.75rem", marginTop: "0.25rem" }}>Across all berth categories</div>
              </div>

              <div style={{ background: "#1e293b", padding: "1.25rem", borderRadius: "10px", border: "1px solid #334155" }}>
                <div style={{ color: "#94a3b8", fontSize: "0.875rem", marginBottom: "0.25rem" }}>Highest Fare</div>
                <div style={{ fontSize: "2rem", fontWeight: "bold", color: "#f43f5e" }}>
                  ₹{data?.summary.max_fare || 0}
                </div>
                <div style={{ color: "#64748b", fontSize: "0.75rem", marginTop: "0.25rem" }}>Premium Single Sleeper</div>
              </div>

              <div style={{ background: "#1e293b", padding: "1.25rem", borderRadius: "10px", border: "1px solid #334155" }}>
                <div style={{ color: "#94a3b8", fontSize: "0.875rem", marginBottom: "0.25rem" }}>Tracked Scrapes</div>
                <div style={{ fontSize: "2rem", fontWeight: "bold", color: "#fbbf24" }}>
                  {data?.total_records || 0}
                </div>
                <div style={{ color: "#64748b", fontSize: "0.75rem", marginTop: "0.25rem" }}>Recorded price observations</div>
              </div>
            </div>

            {/* Seat Type Category Breakdown Grid */}
            <h2 style={{ fontSize: "1.25rem", color: "#f1f5f9", marginBottom: "1rem" }}>
              🛏️ Seat Category Price Breakdown
            </h2>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: "1rem", marginBottom: "2rem" }}>
              {data?.seat_type_breakdown.map((st) => (
                <div
                  key={st.seat_type}
                  style={{
                    background: "#1e293b",
                    padding: "1rem 1.25rem",
                    borderRadius: "8px",
                    border: "1px solid #334155"
                  }}
                >
                  <div style={{ color: "#38bdf8", fontWeight: "bold", textTransform: "capitalize" }}>
                    {st.seat_type.replace("_", " ")} Sleeper
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between", margin: "0.5rem 0" }}>
                    <span style={{ color: "#94a3b8", fontSize: "0.875rem" }}>Avg Fare:</span>
                    <span style={{ color: "#34d399", fontWeight: 600 }}>₹{st.avg_price}</span>
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.875rem" }}>
                    <span style={{ color: "#94a3b8" }}>Range:</span>
                    <span style={{ color: "#cbd5e1" }}>₹{st.min_price} - ₹{st.max_price}</span>
                  </div>
                </div>
              ))}
            </div>

            {/* Filter Bar & Detailed Scraped Fares Table */}
            <div style={{ display: "flex", gap: "1rem", marginBottom: "1rem", flexWrap: "wrap" }}>
              <select
                value={selectedSeatType}
                onChange={(e) => setSelectedSeatType(e.target.value)}
                style={{
                  background: "#1e293b",
                  color: "#f8fafc",
                  border: "1px solid #334155",
                  padding: "0.5rem 1rem",
                  borderRadius: "6px"
                }}
              >
                <option value="all">All Seat Categories</option>
                <option value="single_lower">Single Lower Sleeper</option>
                <option value="single_upper">Single Upper Sleeper</option>
                <option value="double_lower">Double Lower Sleeper</option>
                <option value="double_upper">Double Upper Sleeper</option>
              </select>

              <input
                type="text"
                placeholder="Search bus operator..."
                value={searchOperator}
                onChange={(e) => setSearchOperator(e.target.value)}
                style={{
                  background: "#1e293b",
                  color: "#f8fafc",
                  border: "1px solid #334155",
                  padding: "0.5rem 1rem",
                  borderRadius: "6px",
                  flexGrow: 1,
                  maxWidth: "320px"
                }}
              />
            </div>

            <div style={{ background: "#1e293b", borderRadius: "10px", border: "1px solid #334155", overflow: "hidden" }}>
              <table style={{ width: "100%", borderCollapse: "collapse", textAlign: "left", fontSize: "0.875rem" }}>
                <thead>
                  <tr style={{ background: "#0f172a", color: "#94a3b8", borderBottom: "1px solid #334155" }}>
                    <th style={{ padding: "0.75rem 1rem" }}>Operator</th>
                    <th style={{ padding: "0.75rem 1rem" }}>Bus Type</th>
                    <th style={{ padding: "0.75rem 1rem" }}>Seat Type</th>
                    <th style={{ padding: "0.75rem 1rem" }}>Travel Date</th>
                    <th style={{ padding: "0.75rem 1rem" }}>Fare (₹)</th>
                    <th style={{ padding: "0.75rem 1rem" }}>Seats Left</th>
                    <th style={{ padding: "0.75rem 1rem" }}>Toilet</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredRecords.map((r, idx) => (
                    <tr key={idx} style={{ borderBottom: "1px solid #334155" }}>
                      <td style={{ padding: "0.75rem 1rem", fontWeight: 600, color: "#f1f5f9" }}>{r.operator_name}</td>
                      <td style={{ padding: "0.75rem 1rem", color: "#cbd5e1" }}>{r.bus_type || "A/C Sleeper"}</td>
                      <td style={{ padding: "0.75rem 1rem", color: "#38bdf8", textTransform: "capitalize" }}>
                        {r.seat_type.replace("_", " ")}
                      </td>
                      <td style={{ padding: "0.75rem 1rem", color: "#cbd5e1" }}>{r.travel_date}</td>
                      <td style={{ padding: "0.75rem 1rem", color: "#34d399", fontWeight: "bold" }}>₹{r.price}</td>
                      <td style={{ padding: "0.75rem 1rem", color: "#cbd5e1" }}>{r.available_seats || "-"}</td>
                      <td style={{ padding: "0.75rem 1rem" }}>{r.has_toilet ? "Yes 🚽" : "No"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}
      </div>
    </main>
  );
}
