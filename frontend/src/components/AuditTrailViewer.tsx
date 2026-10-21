import React, { useState, useEffect } from "react";
import { getAuditTrail, verifyAuditChain } from "../api";
import {
  FileText,
  ShieldCheck,
  ShieldAlert,
  Link,
  CheckCircle,
  RefreshCw,
  Search,
  Lock,
} from "lucide-react";

interface AuditLog {
  id: number;
  timestamp: string;
  actor_username: string;
  actor_role: string;
  action: string;
  resource_type: string;
  resource_id: number;
  details: any;
  prev_hash: string;
  current_hash: string;
}

export const AuditTrailViewer: React.FC = () => {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(false);
  const [verifying, setVerifying] = useState(false);
  const [verifyResult, setVerifyResult] = useState<any | null>(null);
  const [actionFilter, setActionFilter] = useState("ALL");
  const [searchQuery, setSearchQuery] = useState("");

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const params: Record<string, any> = {};
      if (actionFilter !== "ALL") {
        params.action = actionFilter;
      }
      const data = await getAuditTrail(params);
      setLogs(data);
    } catch (err) {
      console.error("Failed to load audit logs:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, [actionFilter]);

  const handleVerifyChain = async () => {
    setVerifying(true);
    try {
      const res = await verifyAuditChain();
      setVerifyResult(res);
    } catch (err) {
      console.error("Chain verification failed:", err);
    } finally {
      setVerifying(false);
    }
  };

  const filteredLogs = logs.filter((l) => {
    const q = searchQuery.toLowerCase();
    return (
      l.action.toLowerCase().includes(q) ||
      l.actor_username.toLowerCase().includes(q) ||
      l.current_hash.toLowerCase().includes(q)
    );
  });

  return (
    <div className="tab-pane" id="audit-trail-viewer">
      <div className="section-header">
        <div className="section-title-wrap">
          <h2 className="section-title">
            <Lock style={{ color: "#38bdf8" }} />
            Tamper-Evident SHA-256 Audit Trail & Chain Verification
          </h2>
          <p className="section-desc">
            Append-only cryptographic ledger tracking all generation, screening, human approval, and dissemination events.
          </p>
        </div>

        <div style={{ display: "flex", gap: "0.5rem" }}>
          <button
            className="btn btn-primary btn-sm"
            onClick={handleVerifyChain}
            disabled={verifying}
            id="verify-chain-btn"
          >
            <ShieldCheck size={14} />
            {verifying ? "Verifying Hash Math..." : "Cryptographically Verify Chain Integrity"}
          </button>
          <button className="btn btn-secondary btn-sm" onClick={fetchLogs} disabled={loading}>
            <RefreshCw size={14} className={loading ? "spin" : ""} /> Refresh
          </button>
        </div>
      </div>

      {/* Verification Result Banner */}
      {verifyResult && (
        <div
          className="glass-panel"
          style={{
            padding: "1.25rem",
            marginBottom: "1.25rem",
            background: verifyResult.valid
              ? "rgba(16, 185, 129, 0.12)"
              : "rgba(239, 68, 68, 0.15)",
            border: `1px solid ${verifyResult.valid ? "rgba(16, 185, 129, 0.35)" : "rgba(239, 68, 68, 0.35)"}`,
          }}
          id="verification-result-banner"
        >
          <div style={{ display: "flex", alignItems: "center", gap: "0.6rem" }}>
            {verifyResult.valid ? (
              <ShieldCheck size={24} style={{ color: "#10b981" }} />
            ) : (
              <ShieldAlert size={24} style={{ color: "#ef4444" }} />
            )}
            <div>
              <div style={{ fontWeight: 700, color: verifyResult.valid ? "#34d399" : "#f87171", fontSize: "1rem" }}>
                {verifyResult.valid
                  ? "Cryptographic Chain Verified: Complete Integrity (Zero Tampering Detected)"
                  : "WARNING: Hash Chain Discontinuity Detected!"}
              </div>
              <div style={{ fontSize: "0.82rem", color: "var(--text-secondary)", marginTop: "0.2rem" }}>
                Total Records Verified: <strong>{verifyResult.total_records}</strong> blocks | Latest Head Hash:{" "}
                <span className="font-mono" style={{ color: "#38bdf8" }}>
                  {verifyResult.latest_block_hash?.substring(0, 24)}...
                </span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Filter and Search Controls */}
      <div
        className="glass-panel"
        style={{
          padding: "1rem",
          marginBottom: "1.25rem",
          display: "flex",
          gap: "1rem",
          alignItems: "center",
          flexWrap: "wrap",
        }}
      >
        <div style={{ display: "flex", gap: "0.35rem", flexWrap: "wrap" }}>
          {["ALL", "ADVISORY_GENERATED", "ADVISORY_APPROVED", "ADVISORY_DISSEMINATED", "GUARD_CHECK", "USER_LOGIN"].map(
            (act) => (
              <button
                key={act}
                className={`btn btn-sm ${actionFilter === act ? "btn-primary" : "btn-secondary"}`}
                onClick={() => setActionFilter(act)}
              >
                {act.replace(/_/g, " ")}
              </button>
            )
          )}
        </div>

        <div style={{ marginLeft: "auto", position: "relative", minWidth: "250px" }}>
          <Search size={14} style={{ position: "absolute", left: "10px", top: "11px", color: "var(--text-muted)" }} />
          <input
            type="text"
            className="form-input"
            style={{ height: "36px", paddingLeft: "2rem", fontSize: "0.8rem" }}
            placeholder="Search action, actor, hash..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
      </div>

      {/* Hash Chain Records Table */}
      <div className="glass-panel" style={{ padding: "0.5rem" }}>
        <div className="table-responsive">
          <table className="custom-table" id="audit-logs-table">
            <thead>
              <tr>
                <th>Block #</th>
                <th>Timestamp (UTC)</th>
                <th>Actor & Role</th>
                <th>Action</th>
                <th>Resource</th>
                <th>Cryptographic SHA-256 Hash Chain</th>
              </tr>
            </thead>
            <tbody>
              {filteredLogs.length === 0 ? (
                <tr>
                  <td colSpan={6} style={{ textAlign: "center", padding: "2rem", color: "var(--text-muted)" }}>
                    {loading ? "Loading audit trail..." : "No audit records found."}
                  </td>
                </tr>
              ) : (
                filteredLogs.map((log) => (
                  <tr key={log.id}>
                    <td className="font-mono" style={{ color: "#38bdf8", fontWeight: 700 }}>
                      #{log.id}
                    </td>
                    <td style={{ fontSize: "0.78rem", color: "var(--text-secondary)" }}>
                      {new Date(log.timestamp).toLocaleString()}
                    </td>
                    <td>
                      <div style={{ fontWeight: 600, color: "#fff", fontSize: "0.82rem" }}>
                        {log.actor_username}
                      </div>
                      <div style={{ fontSize: "0.72rem", color: "var(--text-muted)", textTransform: "uppercase" }}>
                        {log.actor_role}
                      </div>
                    </td>
                    <td>
                      <span
                        style={{
                          fontSize: "0.72rem",
                          padding: "0.2rem 0.5rem",
                          borderRadius: "4px",
                          background: log.action.includes("APPROVED")
                            ? "rgba(16, 185, 129, 0.15)"
                            : log.action.includes("DISSEMINATED")
                            ? "rgba(59, 130, 246, 0.15)"
                            : log.action.includes("REJECTED")
                            ? "rgba(239, 68, 68, 0.15)"
                            : "rgba(255, 255, 255, 0.05)",
                          color: log.action.includes("APPROVED")
                            ? "#34d399"
                            : log.action.includes("DISSEMINATED")
                            ? "#60a5fa"
                            : log.action.includes("REJECTED")
                            ? "#f87171"
                            : "#f8fafc",
                          fontWeight: 600,
                        }}
                      >
                        {log.action}
                      </span>
                    </td>
                    <td style={{ fontSize: "0.78rem" }}>
                      {log.resource_type}:{log.resource_id}
                    </td>
                    <td style={{ fontSize: "0.72rem", maxWidth: "340px" }}>
                      <div style={{ display: "flex", alignItems: "center", gap: "0.3rem", color: "#38bdf8" }}>
                        <Link size={11} />
                        <span className="font-mono">Current: {log.current_hash.substring(0, 28)}...</span>
                      </div>
                      <div style={{ color: "var(--text-muted)", marginTop: "2px" }}>
                        <span className="font-mono">Prev: {log.prev_hash.substring(0, 28)}...</span>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
