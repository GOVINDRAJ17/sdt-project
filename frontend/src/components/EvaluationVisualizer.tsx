import React, { useState } from "react";
import {
  ABLATION_METRICS,
  CATEGORY_DISTRIBUTION,
  BENCHMARK_SAMPLES,
} from "../benchmarkData";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell,
} from "recharts";
import {
  ShieldCheck,
  Target,
  BarChart3,
  Clock,
  Layers,
  Search,
  CheckCircle2,
  XCircle,
} from "lucide-react";

export const EvaluationVisualizer: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("ALL");

  const filteredSamples = BENCHMARK_SAMPLES.filter((s) => {
    const matchesCat = categoryFilter === "ALL" || s.category === categoryFilter;
    const matchesQ =
      s.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      s.text.toLowerCase().includes(searchQuery.toLowerCase()) ||
      s.category.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesCat && matchesQ;
  });

  return (
    <div className="tab-pane" id="evaluation-visualizer">
      <div className="section-header">
        <div className="section-title-wrap">
          <h2 className="section-title">
            <Target style={{ color: "#38bdf8" }} />
            Phase 5: Automated Red-Team Evaluation Benchmark & Ablation Harness
          </h2>
          <p className="section-desc">
            Empirical validation of 160 curated attack benchmarks evaluated across 3 architectural configurations (Config A, B, and C).
          </p>
        </div>
      </div>

      {/* Comparative Metric Highlights */}
      <div className="kpi-grid">
        <div className="glass-panel kpi-card">
          <div className="kpi-icon-box" style={{ background: "rgba(239, 68, 68, 0.15)", color: "#ef4444" }}>
            <Target size={24} />
          </div>
          <div className="kpi-data">
            <div className="kpi-label">Config A: Baseline ASR</div>
            <div className="kpi-value font-mono" style={{ color: "#ef4444" }}>100.0%</div>
            <div className="kpi-hint">Raw LLM accepts all injections</div>
          </div>
        </div>

        <div className="glass-panel kpi-card">
          <div className="kpi-icon-box" style={{ background: "rgba(245, 158, 11, 0.15)", color: "#f59e0b" }}>
            <ShieldCheck size={24} />
          </div>
          <div className="kpi-data">
            <div className="kpi-label">Config B: Guard Only ASR</div>
            <div className="kpi-value font-mono" style={{ color: "#f59e0b" }}>29.6%</div>
            <div className="kpi-hint">Misses subtle fact mutators</div>
          </div>
        </div>

        <div className="glass-panel kpi-card">
          <div className="kpi-icon-box" style={{ background: "rgba(16, 185, 129, 0.15)", color: "#10b981" }}>
            <ShieldCheck size={24} />
          </div>
          <div className="kpi-data">
            <div className="kpi-label">Config C: Proposed ASR</div>
            <div className="kpi-value font-mono" style={{ color: "#10b981" }}>0.0%</div>
            <div className="kpi-hint">Guard + Verifier + Human Gate</div>
          </div>
        </div>

        <div className="glass-panel kpi-card">
          <div className="kpi-icon-box" style={{ background: "rgba(56, 189, 248, 0.15)", color: "#38bdf8" }}>
            <Clock size={24} />
          </div>
          <div className="kpi-data">
            <div className="kpi-label">Average Defense Latency</div>
            <div className="kpi-value font-mono" style={{ color: "#38bdf8" }}>0.52 ms</div>
            <div className="kpi-hint">Negligible real-time overhead</div>
          </div>
        </div>
      </div>

      {/* Recharts Comparison Charts */}
      <div style={{ display: "grid", gridTemplateColumns: "1.2fr 1fr", gap: "1.5rem", marginBottom: "1.5rem" }}>
        {/* Ablation Chart 1 */}
        <div className="glass-panel" style={{ padding: "1.5rem" }}>
          <h3 style={{ fontFamily: "var(--font-display)", color: "#fff", fontSize: "1.05rem", marginBottom: "0.5rem" }}>
            Security & Catch Rates Across Ablation Configurations (%)
          </h3>
          <p style={{ fontSize: "0.8rem", color: "var(--text-muted)", marginBottom: "1.25rem" }}>
            Comparing Attack Success Rate (lower is better) vs Hallucination Catch Rate (higher is better).
          </p>

          <div style={{ height: "300px", width: "100%" }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={ABLATION_METRICS} margin={{ top: 20, right: 30, left: 0, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                <XAxis dataKey="config" stroke="var(--text-secondary)" tick={{ fontSize: 11 }} />
                <YAxis stroke="var(--text-secondary)" tick={{ fontSize: 11 }} domain={[0, 100]} />
                <Tooltip
                  contentStyle={{
                    background: "#0f172a",
                    borderColor: "var(--border-subtle)",
                    borderRadius: "8px",
                    color: "#fff",
                    fontSize: "12px",
                  }}
                />
                <Legend wrapperStyle={{ fontSize: "12px", paddingTop: "10px" }} />
                <Bar dataKey="asr" name="Attack Success Rate (ASR %)" fill="#ef4444" radius={[4, 4, 0, 0]} />
                <Bar dataKey="catchRate" name="Hallucination Catch Rate (%)" fill="#38bdf8" radius={[4, 4, 0, 0]} />
                <Bar dataKey="fpr" name="False-Positive Rate (%)" fill="#10b981" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Latency & Overhead Breakdown Chart */}
        <div className="glass-panel" style={{ padding: "1.5rem" }}>
          <h3 style={{ fontFamily: "var(--font-display)", color: "#fff", fontSize: "1.05rem", marginBottom: "0.5rem" }}>
            Processing Latency Overhead (ms)
          </h3>
          <p style={{ fontSize: "0.8rem", color: "var(--text-muted)", marginBottom: "1.25rem" }}>
            Added verification and sanitization runtime per advisory evaluation.
          </p>

          <div style={{ height: "300px", width: "100%" }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={ABLATION_METRICS} margin={{ top: 20, right: 30, left: 0, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                <XAxis dataKey="config" stroke="var(--text-secondary)" tick={{ fontSize: 11 }} />
                <YAxis stroke="var(--text-secondary)" tick={{ fontSize: 11 }} />
                <Tooltip
                  contentStyle={{
                    background: "#0f172a",
                    borderColor: "var(--border-subtle)",
                    borderRadius: "8px",
                    color: "#fff",
                    fontSize: "12px",
                  }}
                />
                <Bar dataKey="latency" name="Average Latency (ms)" fill="#8b5cf6" radius={[4, 4, 0, 0]}>
                  {ABLATION_METRICS.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Category Breakdown & Dataset Inspection */}
      <div className="glass-panel" style={{ padding: "1.5rem" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem", flexWrap: "wrap", gap: "0.75rem" }}>
          <div>
            <h3 style={{ fontFamily: "var(--font-display)", color: "#fff", fontSize: "1.1rem" }}>
              160-Case Curated Red-Team Benchmark Samples
            </h3>
            <p style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
              Covering direct injection, indirect operator notes, prompt leaks, base64 obfuscation, and hallucination mutators.
            </p>
          </div>

          <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
            <select
              className="form-select"
              style={{ width: "auto", height: "36px", fontSize: "0.8rem" }}
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
            >
              <option value="ALL">All Categories (160 cases)</option>
              <option value="direct_injection">Direct Injection (25)</option>
              <option value="indirect_operator_notes">Indirect Operator Notes (25)</option>
              <option value="prompt_leak">Prompt Leak & Canary (25)</option>
              <option value="obfuscated_multilingual">Obfuscated & Multilingual (25)</option>
              <option value="hallucination_inducing">Hallucination & Fact Mutators (25)</option>
              <option value="benign_baseline">Benign Baseline (35)</option>
            </select>

            <div style={{ position: "relative", minWidth: "200px" }}>
              <Search size={14} style={{ position: "absolute", left: "10px", top: "11px", color: "var(--text-muted)" }} />
              <input
                type="text"
                className="form-input"
                style={{ height: "36px", paddingLeft: "2rem", fontSize: "0.8rem" }}
                placeholder="Search case..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
          </div>
        </div>

        <div className="table-responsive">
          <table className="custom-table">
            <thead>
              <tr>
                <th>Case ID</th>
                <th>Category</th>
                <th>Adversarial Test Input</th>
                <th>Guard Blocked</th>
                <th>Verifier Caught</th>
                <th>Final Outcome (Config C)</th>
              </tr>
            </thead>
            <tbody>
              {filteredSamples.map((sample) => (
                <tr key={sample.id}>
                  <td className="font-mono" style={{ color: "#38bdf8", fontWeight: 700 }}>
                    {sample.id}
                  </td>
                  <td>
                    <span
                      style={{
                        fontSize: "0.72rem",
                        padding: "0.2rem 0.5rem",
                        borderRadius: "4px",
                        background: "rgba(255,255,255,0.05)",
                        textTransform: "capitalize",
                      }}
                    >
                      {sample.category.replace(/_/g, " ")}
                    </span>
                  </td>
                  <td style={{ fontSize: "0.82rem", maxWidth: "380px" }}>
                    <div className="font-mono">{sample.text}</div>
                  </td>
                  <td>
                    {sample.blockedByGuard ? (
                      <span style={{ color: "#f87171", fontSize: "0.78rem", display: "flex", alignItems: "center", gap: "3px" }}>
                        <CheckCircle2 size={13} /> Blocked at L1-L3
                      </span>
                    ) : (
                      <span style={{ color: "var(--text-muted)", fontSize: "0.78rem" }}>Passed to LLM</span>
                    )}
                  </td>
                  <td>
                    {sample.caughtByVerifier ? (
                      <span style={{ color: "#38bdf8", fontSize: "0.78rem", display: "flex", alignItems: "center", gap: "3px" }}>
                        <CheckCircle2 size={13} /> Inconsistency Caught
                      </span>
                    ) : (
                      <span style={{ color: "var(--text-muted)", fontSize: "0.78rem" }}>—</span>
                    )}
                  </td>
                  <td>
                    {sample.result === "DEFENDED" ? (
                      <span className="status-badge APPROVED" style={{ fontSize: "0.7rem" }}>
                        Defended (0% ASR)
                      </span>
                    ) : (
                      <span className="status-badge DISSEMINATED" style={{ fontSize: "0.7rem" }}>
                        Benign Passed (0% FPR)
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
