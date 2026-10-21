import React, { useState, useEffect } from "react";
import {
  loginUser,
  getSystemHealth,
  getOperationalMetrics,
  getCurrentUser,
  setAuthToken,
} from "./api";
import { ReviewerPortal } from "./components/ReviewerPortal";
import { AdvisoryGenerator } from "./components/AdvisoryGenerator";
import { ForecastExplorer } from "./components/ForecastExplorer";
import { InputGuardSandbox } from "./components/InputGuardSandbox";
import { EvaluationVisualizer } from "./components/EvaluationVisualizer";
import { AuditTrailViewer } from "./components/AuditTrailViewer";
import { GovernanceViewer } from "./components/GovernanceViewer";
import {
  Flame,
  FileCheck2,
  Sparkles,
  CloudSun,
  ShieldAlert,
  Target,
  Lock,
  Scale,
  User,
  Activity,
  CheckCircle2,
  Layers,
} from "lucide-react";

type TabId =
  | "reviewer"
  | "generator"
  | "forecasts"
  | "guard"
  | "evaluation"
  | "audit"
  | "governance";

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<TabId>("reviewer");
  const [currentRole, setCurrentRole] = useState<string>("meteorologist");
  const [currentUser, setCurrentUser] = useState<string>("meteorologist@imd.gov.in");
  const [systemOnline, setSystemOnline] = useState<boolean>(true);
  const [metrics, setMetrics] = useState<any | null>(null);

  // Auto-login to meteorologist account by default on load
  const switchAccount = async (roleName: string) => {
    let username = "meteorologist@imd.gov.in";
    let password = "meteo123";

    if (roleName === "admin") {
      username = "admin@imd.gov.in";
      password = "admin123";
    } else if (roleName === "viewer") {
      username = "viewer@imd.gov.in";
      password = "viewer123";
    }

    try {
      const res = await loginUser(username, password);
      setCurrentRole(res.role);
      setCurrentUser(res.username);
      await fetchMetrics();
    } catch (err) {
      console.error("Account switch failed:", err);
      setCurrentRole(roleName);
      setCurrentUser(username);
    }
  };

  const fetchMetrics = async () => {
    try {
      const data = await getOperationalMetrics();
      setMetrics(data);
    } catch (err) {
      console.warn("Metrics fetch error:", err);
    }
  };

  const checkHealth = async () => {
    try {
      await getSystemHealth();
      setSystemOnline(true);
    } catch {
      setSystemOnline(false);
    }
  };

  useEffect(() => {
    switchAccount("meteorologist");
    checkHealth();
    fetchMetrics();
    const interval = setInterval(() => {
      fetchMetrics();
      checkHealth();
    }, 12000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="app-container">
      {/* Executive Header */}
      <header className="top-header">
        <div className="header-content">
          <div className="brand-section">
            <div className="brand-logo-badge">
              <Flame size={24} />
            </div>
            <div>
              <div className="brand-title">
                IMD-CES Secure Heatwave Advisory Portal
                <span className="brand-tag">KJS-CES-01</span>
              </div>
              <div className="brand-subtitle">
                Academic & Research AI Platform • India Meteorological Department & K J Somaiya
              </div>
            </div>
          </div>

          <div className="header-actions">
            {/* System Health */}
            <div className="system-status-pill">
              <div className={`status-dot ${systemOnline ? "" : "offline"}`} />
              {systemOnline ? "FastAPI Core Active" : "Backend Offline"}
            </div>

            {/* Role Switcher */}
            <div className="role-switcher">
              <button
                className={`role-btn ${currentRole === "meteorologist" ? "active" : ""}`}
                onClick={() => switchAccount("meteorologist")}
                id="role-meteorologist-btn"
                title="Certified Senior Meteorologist (Approver & Disseminator)"
              >
                <User size={13} /> Meteorologist
              </button>

              <button
                className={`role-btn ${currentRole === "admin" ? "active" : ""}`}
                onClick={() => switchAccount("admin")}
                id="role-admin-btn"
                title="System Administrator"
              >
                Admin
              </button>

              <button
                className={`role-btn ${currentRole === "viewer" ? "active" : ""}`}
                onClick={() => switchAccount("viewer")}
                id="role-viewer-btn"
                title="General Public Viewer (Read-only)"
              >
                Viewer
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Navigation Tab Strip */}
      <nav className="nav-tab-strip">
        <div className="tabs-inner">
          <button
            className={`tab-link ${activeTab === "reviewer" ? "active" : ""}`}
            onClick={() => setActiveTab("reviewer")}
            id="nav-reviewer-tab"
          >
            <FileCheck2 size={16} />
            Reviewer Queue
            {metrics?.advisories?.pending_review > 0 && (
              <span className="tab-badge">{metrics.advisories.pending_review}</span>
            )}
          </button>

          <button
            className={`tab-link ${activeTab === "generator" ? "active" : ""}`}
            onClick={() => setActiveTab("generator")}
            id="nav-generator-tab"
          >
            <Sparkles size={16} />
            Advisory Generator
          </button>

          <button
            className={`tab-link ${activeTab === "forecasts" ? "active" : ""}`}
            onClick={() => setActiveTab("forecasts")}
            id="nav-forecasts-tab"
          >
            <CloudSun size={16} />
            Forecast Explorer & Rules
          </button>

          <button
            className={`tab-link ${activeTab === "guard" ? "active" : ""}`}
            onClick={() => setActiveTab("guard")}
            id="nav-guard-tab"
          >
            <ShieldAlert size={16} />
            Input Guard Sandbox
          </button>

          <button
            className={`tab-link ${activeTab === "evaluation" ? "active" : ""}`}
            onClick={() => setActiveTab("evaluation")}
            id="nav-evaluation-tab"
          >
            <Target size={16} />
            Phase 5 Evaluation & Ablation
          </button>

          <button
            className={`tab-link ${activeTab === "audit" ? "active" : ""}`}
            onClick={() => setActiveTab("audit")}
            id="nav-audit-tab"
          >
            <Lock size={16} />
            Audit Ledger (SHA-256)
          </button>

          <button
            className={`tab-link ${activeTab === "governance" ? "active" : ""}`}
            onClick={() => setActiveTab("governance")}
            id="nav-governance-tab"
          >
            <Scale size={16} />
            STRIDE & DPDP Act 2023
          </button>
        </div>
      </nav>

      {/* Main Container */}
      <main className="main-content">
        {/* Real-time KPI Bar */}
        {metrics && (
          <div className="kpi-grid">
            <div className="glass-panel kpi-card">
              <div className="kpi-icon-box" style={{ background: "rgba(56, 189, 248, 0.15)", color: "#38bdf8" }}>
                <CloudSun size={24} />
              </div>
              <div className="kpi-data">
                <div className="kpi-label">Weather Forecasts</div>
                <div className="kpi-value font-mono">{metrics.forecasts?.total_forecasts ?? 0}</div>
                <div className="kpi-hint">AWS Synoptic Stations</div>
              </div>
            </div>

            <div className="glass-panel kpi-card">
              <div className="kpi-icon-box" style={{ background: "rgba(245, 158, 11, 0.15)", color: "#f59e0b" }}>
                <FileCheck2 size={24} />
              </div>
              <div className="kpi-data">
                <div className="kpi-label">Pending Review</div>
                <div className="kpi-value font-mono" style={{ color: "#f59e0b" }}>
                  {metrics.advisories?.pending_review ?? 0}
                </div>
                <div className="kpi-hint">Meteorologist Sign-off Gate</div>
              </div>
            </div>

            <div className="glass-panel kpi-card">
              <div className="kpi-icon-box" style={{ background: "rgba(59, 130, 246, 0.15)", color: "#60a5fa" }}>
                <Activity size={24} />
              </div>
              <div className="kpi-data">
                <div className="kpi-label">Disseminated Warnings</div>
                <div className="kpi-value font-mono" style={{ color: "#60a5fa" }}>
                  {metrics.advisories?.disseminated ?? 0}
                </div>
                <div className="kpi-hint">Multi-Channel Broadcasts</div>
              </div>
            </div>

            <div className="glass-panel kpi-card">
              <div className="kpi-icon-box" style={{ background: "rgba(16, 185, 129, 0.15)", color: "#10b981" }}>
                <Lock size={24} />
              </div>
              <div className="kpi-data">
                <div className="kpi-label">Audit Trail Integrity</div>
                <div className="kpi-value font-mono" style={{ color: "#10b981", fontSize: "1.2rem" }}>
                  {metrics.security_and_governance?.tamper_evident_chain_integrity ? "100% INTACT" : "DISCONTINUITY"}
                </div>
                <div className="kpi-hint">{metrics.security_and_governance?.total_audit_records ?? 0} SHA-256 Blocks</div>
              </div>
            </div>
          </div>
        )}

        {/* Dynamic Tab Panes */}
        {activeTab === "reviewer" && (
          <ReviewerPortal currentRole={currentRole} onRefreshMetrics={fetchMetrics} />
        )}

        {activeTab === "generator" && (
          <AdvisoryGenerator onAdvisoryCreated={fetchMetrics} />
        )}

        {activeTab === "forecasts" && <ForecastExplorer />}

        {activeTab === "guard" && <InputGuardSandbox />}

        {activeTab === "evaluation" && <EvaluationVisualizer />}

        {activeTab === "audit" && <AuditTrailViewer />}

        {activeTab === "governance" && <GovernanceViewer />}
      </main>

      {/* Footer */}
      <footer style={{ borderTop: "1px solid var(--border-subtle)", padding: "1.5rem 2rem", textAlign: "center", fontSize: "0.8rem", color: "var(--text-muted)" }}>
        <div>
          K J Somaiya Institute - AI Use Case Integration in Teaching-Learning (KJS-CES-01) in collaboration with India Meteorological Department (IMD).
        </div>
        <div style={{ marginTop: "0.25rem" }}>
          Ground-Truth Verifier • Deterministic Rule Engine • Multi-Layer Security Guard • Tamper-Evident SHA-256 Audit Chain
        </div>
      </footer>
    </div>
  );
};
