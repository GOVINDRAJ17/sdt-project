import React, { useState, useEffect } from "react";
import { listForecasts, evaluateRuleEngine } from "../api";
import {
  CloudSun,
  Thermometer,
  Sliders,
  CheckCircle,
  AlertCircle,
  MapPin,
  RefreshCw,
} from "lucide-react";

interface ForecastRecord {
  id: number;
  region_name: string;
  region_type: string;
  date: string;
  forecast_tmax_c: number;
  normal_tmax_c: number;
  departure_c: number;
  severity: string;
  confidence: number;
  lead_time_days: number;
}

export const ForecastExplorer: React.FC = () => {
  const [forecasts, setForecasts] = useState<ForecastRecord[]>([]);
  const [loading, setLoading] = useState(false);

  // Simulator State
  const [simRegionType, setSimRegionType] = useState<string>("plains");
  const [simTmax, setSimTmax] = useState<number>(46.2);
  const [simNormal, setSimNormal] = useState<number>(40.5);
  const [simResult, setSimResult] = useState<any | null>(null);

  const fetchForecasts = async () => {
    setLoading(true);
    try {
      const data = await listForecasts();
      setForecasts(data);
    } catch (err) {
      console.error("Failed to load forecasts:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchForecasts();
  }, []);

  // Update simulator whenever sliders change
  useEffect(() => {
    const runSimulation = async () => {
      try {
        const res = await evaluateRuleEngine({
          region_type: simRegionType,
          forecast_tmax_c: Number(simTmax),
          normal_tmax_c: Number(simNormal),
        });
        setSimResult(res);
      } catch (err) {
        console.error("Simulator evaluation failed:", err);
      }
    };
    runSimulation();
  }, [simRegionType, simTmax, simNormal]);

  return (
    <div className="tab-pane" id="forecast-explorer">
      <div className="section-header">
        <div className="section-title-wrap">
          <h2 className="section-title">
            <CloudSun style={{ color: "#38bdf8" }} />
            Forecast Explorer & IMD Deterministic Rule Engine
          </h2>
          <p className="section-desc">
            Official India Meteorological Department (IMD) scientific criteria for Plains, Hilly, and Coastal divisions.
          </p>
        </div>

        <button className="btn btn-secondary btn-sm" onClick={fetchForecasts} disabled={loading}>
          <RefreshCw size={14} className={loading ? "spin" : ""} /> Refresh
        </button>
      </div>

      {/* IMD Rule Engine Interactive Simulator */}
      <div
        className="glass-panel"
        style={{
          padding: "1.5rem",
          marginBottom: "1.5rem",
          background: "linear-gradient(135deg, rgba(16, 24, 46, 0.85) 0%, rgba(26, 38, 74, 0.6) 100%)",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "1rem" }}>
          <Sliders size={20} style={{ color: "#38bdf8" }} />
          <h3 style={{ fontFamily: "var(--font-display)", color: "#fff", fontSize: "1.1rem" }}>
            Live IMD Criteria Threshold Simulator
          </h3>
          <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginLeft: "auto" }}>
            Evaluated deterministically in Python backend
          </span>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1.2fr 1fr", gap: "1.5rem" }}>
          {/* Controls */}
          <div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr", gap: "1rem" }}>
              <div className="form-group">
                <label className="form-label">Division / Region Type:</label>
                <div style={{ display: "flex", gap: "0.5rem" }}>
                  {[
                    { id: "plains", label: "Plains (Tmax ≥ 40°C)" },
                    { id: "coastal", label: "Coastal (Tmax ≥ 37°C)" },
                    { id: "hilly", label: "Hilly (Tmax ≥ 30°C)" },
                  ].map((r) => (
                    <button
                      key={r.id}
                      type="button"
                      className={`btn btn-sm ${simRegionType === r.id ? "btn-primary" : "btn-secondary"}`}
                      style={{ flex: 1 }}
                      onClick={() => setSimRegionType(r.id)}
                    >
                      {r.label}
                    </button>
                  ))}
                </div>
              </div>

              <div className="form-group">
                <div style={{ display: "flex", justifyContent: "space-between" }}>
                  <label className="form-label">Forecast Maximum Temperature (Tmax):</label>
                  <span className="font-mono" style={{ color: "#f87171", fontWeight: 700 }}>
                    {simTmax}°C
                  </span>
                </div>
                <input
                  type="range"
                  min="20"
                  max="52"
                  step="0.1"
                  value={simTmax}
                  onChange={(e) => setSimTmax(parseFloat(e.target.value))}
                  style={{ width: "100%", accentColor: "#ef4444" }}
                />
              </div>

              <div className="form-group">
                <div style={{ display: "flex", justifyContent: "space-between" }}>
                  <label className="form-label">Climatological Normal Maximum (Normal):</label>
                  <span className="font-mono" style={{ color: "#38bdf8", fontWeight: 700 }}>
                    {simNormal}°C
                  </span>
                </div>
                <input
                  type="range"
                  min="20"
                  max="45"
                  step="0.1"
                  value={simNormal}
                  onChange={(e) => setSimNormal(parseFloat(e.target.value))}
                  style={{ width: "100%", accentColor: "#38bdf8" }}
                />
              </div>
            </div>
          </div>

          {/* Outcome Gauge */}
          {simResult && (
            <div
              style={{
                background: "rgba(0,0,0,0.35)",
                border: "1px solid var(--border-subtle)",
                borderRadius: "12px",
                padding: "1.25rem",
                display: "flex",
                flexDirection: "column",
                justifyContent: "space-between",
              }}
            >
              <div>
                <div style={{ fontSize: "0.78rem", color: "var(--text-muted)", textTransform: "uppercase" }}>
                  IMD Computed Severity Classification
                </div>
                <div style={{ margin: "0.5rem 0" }}>
                  <span
                    className={`severity-pill ${simResult.severity}`}
                    style={{ fontSize: "1rem", padding: "0.4rem 1rem" }}
                  >
                    {simResult.severity.replace("_", " ")}
                  </span>
                </div>

                <div
                  style={{
                    display: "grid",
                    gridTemplateColumns: "1fr 1fr",
                    gap: "0.75rem",
                    margin: "0.75rem 0",
                    fontSize: "0.85rem",
                  }}
                >
                  <div>
                    <span style={{ color: "var(--text-muted)" }}>Departure (ΔT): </span>
                    <strong className="font-mono" style={{ color: simResult.departure_c >= 4.5 ? "#f59e0b" : "#34d399" }}>
                      {simResult.departure_c > 0 ? `+${simResult.departure_c.toFixed(1)}` : simResult.departure_c.toFixed(1)}°C
                    </strong>
                  </div>
                  <div>
                    <span style={{ color: "var(--text-muted)" }}>Region Criteria: </span>
                    <strong style={{ textTransform: "capitalize" }}>{simResult.region_type}</strong>
                  </div>
                </div>

                <div style={{ fontSize: "0.78rem", color: "var(--text-muted)", marginTop: "0.5rem" }}>
                  Triggered Meteorological Criteria:
                </div>
                <ul style={{ paddingLeft: "1.1rem", fontSize: "0.8rem", color: "#38bdf8", marginTop: "0.25rem" }}>
                  {simResult.criteria_triggered.map((c: string, idx: number) => (
                    <li key={idx} style={{ color: "var(--text-primary)", marginBottom: "0.2rem" }}>
                      {c}
                    </li>
                  ))}
                </ul>
              </div>

              <div style={{ fontSize: "0.72rem", color: "var(--text-muted)", fontStyle: "italic", marginTop: "0.75rem" }}>
                {simResult.disclaimer}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Regional Station Forecasts Grid */}
      <h3 style={{ fontFamily: "var(--font-display)", color: "#fff", fontSize: "1.15rem", marginBottom: "1rem" }}>
        Active Meteorological Station Telemetry & Synoptic Forecasts
      </h3>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))", gap: "1.25rem" }}>
        {forecasts.map((f) => (
          <div key={f.id} className="glass-panel" style={{ padding: "1.25rem" }} id={`forecast-card-${f.id}`}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "0.75rem" }}>
              <div>
                <div style={{ display: "flex", alignItems: "center", gap: "0.4rem", fontWeight: 700, color: "#fff" }}>
                  <MapPin size={15} style={{ color: "#38bdf8" }} />
                  {f.region_name}
                </div>
                <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: "2px", textTransform: "capitalize" }}>
                  {f.region_type} Zone • {f.date}
                </div>
              </div>
              <span className={`severity-pill ${f.severity}`}>{f.severity.replace("_", " ")}</span>
            </div>

            <div style={{ display: "flex", alignItems: "baseline", gap: "0.5rem", margin: "1rem 0" }}>
              <Thermometer size={24} style={{ color: f.severity === "SEVERE_HEATWAVE" ? "#ef4444" : f.severity === "HEATWAVE" ? "#f59e0b" : "#10b981" }} />
              <span className="font-mono" style={{ fontSize: "2rem", fontWeight: 700, color: "#fff" }}>
                {f.forecast_tmax_c}°C
              </span>
              <span style={{ fontSize: "0.85rem", color: "var(--text-secondary)" }}>
                (Normal: {f.normal_tmax_c}°C)
              </span>
            </div>

            <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.78rem", color: "var(--text-secondary)", borderTop: "1px solid var(--border-subtle)", paddingTop: "0.75rem" }}>
              <div>
                Departure:{" "}
                <strong style={{ color: f.departure_c >= 4.5 ? "#f59e0b" : "#34d399" }}>
                  {f.departure_c > 0 ? `+${f.departure_c.toFixed(1)}` : f.departure_c.toFixed(1)}°C
                </strong>
              </div>
              <div>
                Confidence: <strong>{(f.confidence * 100).toFixed(0)}%</strong>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
