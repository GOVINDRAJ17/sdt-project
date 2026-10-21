import React, { useState, useEffect } from "react";
import {
  listAdvisories,
  approveAdvisory,
  rejectAdvisory,
  disseminateAdvisory,
} from "../api";
import {
  CheckCircle2,
  XCircle,
  Send,
  AlertTriangle,
  ShieldCheck,
  RefreshCw,
  Search,
  Eye,
  FileCheck2,
  ExternalLink,
} from "lucide-react";

interface Advisory {
  id: number;
  forecast_id?: number;
  stakeholder: string;
  language: string;
  severity: string;
  region_name: string;
  date: string;
  tmax_c: number;
  headline: string;
  body: string;
  actions: string[];
  uncertainty_statement: string;
  verification_passed: boolean;
  verification_details?: any;
  is_fallback: boolean;
  regeneration_count: number;
  status: string;
  reviewed_by?: string;
  reviewed_at?: string;
  review_comments?: string;
  disseminated_at?: string;
  created_at: string;
}

interface Props {
  currentRole: string;
  onRefreshMetrics: () => void;
}

export const ReviewerPortal: React.FC<Props> = ({ currentRole, onRefreshMetrics }) => {
  const [advisories, setAdvisories] = useState<Advisory[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedAdvisory, setSelectedAdvisory] = useState<Advisory | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState("");
  const [actionLoading, setActionLoading] = useState(false);
  const [reviewComment, setReviewComment] = useState("");
  const [rejectReason, setRejectReason] = useState("");
  const [showRejectModal, setShowRejectModal] = useState(false);
  const [disseminationResult, setDisseminationResult] = useState<any | null>(null);

  const fetchAdvisories = async () => {
    setLoading(true);
    try {
      const params: Record<string, any> = {};
      if (statusFilter !== "ALL") {
        params.status = statusFilter;
      }
      const data = await listAdvisories(params);
      setAdvisories(data);
      if (selectedAdvisory) {
        const updated = data.find((a: Advisory) => a.id === selectedAdvisory.id);
        if (updated) setSelectedAdvisory(updated);
      }
    } catch (err) {
      console.error("Failed to load advisories:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAdvisories();
  }, [statusFilter]);

  const handleApprove = async () => {
    if (!selectedAdvisory) return;
    setActionLoading(true);
    try {
      const updated = await approveAdvisory(selectedAdvisory.id, reviewComment || "Meteorological criteria verified against ground truth");
      setSelectedAdvisory(updated);
      setReviewComment("");
      await fetchAdvisories();
      onRefreshMetrics();
    } catch (err: any) {
      alert(`Approval failed: ${err.message}`);
    } finally {
      setActionLoading(false);
    }
  };

  const handleReject = async () => {
    if (!selectedAdvisory || !rejectReason.trim()) return;
    setActionLoading(true);
    try {
      const updated = await rejectAdvisory(selectedAdvisory.id, rejectReason);
      setSelectedAdvisory(updated);
      setShowRejectModal(false);
      setRejectReason("");
      await fetchAdvisories();
      onRefreshMetrics();
    } catch (err: any) {
      alert(`Rejection failed: ${err.message}`);
    } finally {
      setActionLoading(false);
    }
  };

  const handleDisseminate = async () => {
    if (!selectedAdvisory) return;
    setActionLoading(true);
    try {
      const res = await disseminateAdvisory(selectedAdvisory.id);
      setDisseminationResult(res.dissemination_details);
      await fetchAdvisories();
      onRefreshMetrics();
    } catch (err: any) {
      alert(`Dissemination failed: ${err.message}`);
    } finally {
      setActionLoading(false);
    }
  };

  const filteredAdvisories = advisories.filter((a) => {
    const q = searchQuery.toLowerCase();
    return (
      a.region_name.toLowerCase().includes(q) ||
      a.headline.toLowerCase().includes(q) ||
      a.severity.toLowerCase().includes(q) ||
      a.stakeholder.toLowerCase().includes(q)
    );
  });

  const canReview = currentRole === "meteorologist" || currentRole === "admin";

  return (
    <div className="tab-pane" id="reviewer-portal">
      <div className="section-header">
        <div className="section-title-wrap">
          <h2 className="section-title">
            <FileCheck2 style={{ color: "#38bdf8" }} />
            Human-in-the-Loop Advisory Review Queue
          </h2>
          <p className="section-desc">
            Mandatory meteorologist verification checkpoint before multi-channel dissemination. Ground-truth verified against IMD criteria.
          </p>
        </div>

        <div style={{ display: "flex", gap: "0.5rem" }}>
          <button
            className="btn btn-secondary btn-sm"
            onClick={fetchAdvisories}
            disabled={loading}
            id="refresh-advisories-btn"
          >
            <RefreshCw size={14} className={loading ? "spin" : ""} /> Refresh
          </button>
        </div>
      </div>

      {/* Filter and Search Bar */}
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
          {["ALL", "PENDING_REVIEW", "APPROVED", "DISSEMINATED", "REJECTED"].map((st) => (
            <button
              key={st}
              className={`btn btn-sm ${statusFilter === st ? "btn-primary" : "btn-secondary"}`}
              onClick={() => setStatusFilter(st)}
              id={`filter-${st.toLowerCase()}`}
            >
              {st.replace("_", " ")}
            </button>
          ))}
        </div>

        <div style={{ marginLeft: "auto", position: "relative", minWidth: "260px" }}>
          <Search
            size={16}
            style={{ position: "absolute", left: "10px", top: "10px", color: "var(--text-muted)" }}
          />
          <input
            type="text"
            className="form-input"
            style={{ paddingLeft: "2.2rem", paddingRight: "0.8rem", height: "36px" }}
            placeholder="Search region, headline..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            id="search-advisories-input"
          />
        </div>
      </div>

      {/* Main Grid: List + Detail Inspector */}
      <div style={{ display: "grid", gridTemplateColumns: selectedAdvisory ? "1fr 1.25fr" : "1fr", gap: "1.25rem" }}>
        {/* Advisories Table / List */}
        <div className="glass-panel" style={{ padding: "0.5rem" }}>
          <div className="table-responsive">
            <table className="custom-table" id="advisories-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Region / Date</th>
                  <th>Severity</th>
                  <th>Stakeholder</th>
                  <th>Status</th>
                  <th>Verification</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {filteredAdvisories.length === 0 ? (
                  <tr>
                    <td colSpan={7} style={{ textAlign: "center", padding: "2rem", color: "var(--text-muted)" }}>
                      {loading ? "Loading advisories..." : "No advisories found matching criteria."}
                    </td>
                  </tr>
                ) : (
                  filteredAdvisories.map((adv) => (
                    <tr
                      key={adv.id}
                      style={{
                        cursor: "pointer",
                        background: selectedAdvisory?.id === adv.id ? "rgba(56, 189, 248, 0.08)" : undefined,
                      }}
                      onClick={() => setSelectedAdvisory(adv)}
                      id={`advisory-row-${adv.id}`}
                    >
                      <td className="font-mono">#{adv.id}</td>
                      <td>
                        <strong>{adv.region_name}</strong>
                        <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>{adv.date}</div>
                      </td>
                      <td>
                        <span className={`severity-pill ${adv.severity}`}>{adv.severity.replace("_", " ")}</span>
                      </td>
                      <td style={{ textTransform: "capitalize" }}>
                        {adv.stakeholder.replace("_", " ")}
                        <span style={{ fontSize: "0.72rem", color: "var(--text-muted)", marginLeft: "4px" }}>
                          ({adv.language.toUpperCase()})
                        </span>
                      </td>
                      <td>
                        <span className={`status-badge ${adv.status}`}>{adv.status.replace("_", " ")}</span>
                      </td>
                      <td>
                        {adv.is_fallback ? (
                          <span
                            style={{
                              fontSize: "0.72rem",
                              color: "#f59e0b",
                              display: "inline-flex",
                              alignItems: "center",
                              gap: "3px",
                            }}
                          >
                            <AlertTriangle size={13} /> Fallback Safe
                          </span>
                        ) : adv.verification_passed ? (
                          <span
                            style={{
                              fontSize: "0.72rem",
                              color: "#10b981",
                              display: "inline-flex",
                              alignItems: "center",
                              gap: "3px",
                            }}
                          >
                            <ShieldCheck size={13} /> Ground Truth Pass
                          </span>
                        ) : (
                          <span style={{ fontSize: "0.72rem", color: "#ef4444" }}>Failed</span>
                        )}
                      </td>
                      <td>
                        <button
                          className="btn btn-secondary btn-sm"
                          onClick={(e) => {
                            e.stopPropagation();
                            setSelectedAdvisory(adv);
                          }}
                        >
                          <Eye size={13} /> View
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Selected Advisory Detail Inspector */}
        {selectedAdvisory && (
          <div className="glass-panel" style={{ padding: "1.5rem" }} id="advisory-detail-card">
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "flex-start",
                borderBottom: "1px solid var(--border-subtle)",
                paddingBottom: "1rem",
                marginBottom: "1.25rem",
              }}
            >
              <div>
                <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.25rem" }}>
                  <span className="font-mono" style={{ color: "#38bdf8", fontWeight: 700 }}>
                    Advisory #{selectedAdvisory.id}
                  </span>
                  <span className={`severity-pill ${selectedAdvisory.severity}`}>
                    {selectedAdvisory.severity.replace("_", " ")}
                  </span>
                  <span className={`status-badge ${selectedAdvisory.status}`}>
                    {selectedAdvisory.status.replace("_", " ")}
                  </span>
                </div>
                <div style={{ fontSize: "0.85rem", color: "var(--text-secondary)" }}>
                  Target: <strong>{selectedAdvisory.region_name}</strong> | Date: <strong>{selectedAdvisory.date}</strong> |
                  Max Temp: <strong>{selectedAdvisory.tmax_c}°C</strong>
                </div>
              </div>

              <button
                className="btn btn-secondary btn-sm"
                onClick={() => setSelectedAdvisory(null)}
                style={{ padding: "0.2rem 0.5rem" }}
              >
                ✕
              </button>
            </div>

            {/* Warning if Fallback was triggered */}
            {selectedAdvisory.is_fallback && (
              <div
                style={{
                  background: "rgba(245, 158, 11, 0.12)",
                  border: "1px solid rgba(245, 158, 11, 0.35)",
                  borderRadius: "8px",
                  padding: "0.75rem 1rem",
                  marginBottom: "1rem",
                  display: "flex",
                  gap: "0.6rem",
                  alignItems: "flex-start",
                }}
              >
                <AlertTriangle size={18} style={{ color: "#f59e0b", flexShrink: 0, marginTop: "2px" }} />
                <div style={{ fontSize: "0.82rem", color: "#fbbf24" }}>
                  <strong>Deterministic Safe Fallback Engaged:</strong> Candidate LLM generated output failed ground-truth verification after {selectedAdvisory.regeneration_count} retry attempt(s). Dispatched IMD pre-approved verified template to eliminate hallucination risk.
                </div>
              </div>
            )}

            {/* Generated Advisory Text */}
            <div style={{ marginBottom: "1.25rem" }}>
              <div style={{ fontSize: "0.78rem", textTransform: "uppercase", color: "var(--text-muted)", fontWeight: 600 }}>
                Advisory Headline
              </div>
              <h3 style={{ fontFamily: "var(--font-display)", fontSize: "1.15rem", color: "#fff", margin: "0.3rem 0 0.8rem 0" }}>
                {selectedAdvisory.headline}
              </h3>

              <div style={{ fontSize: "0.78rem", textTransform: "uppercase", color: "var(--text-muted)", fontWeight: 600 }}>
                Context & Meteorological Advisory Body
              </div>
              <p style={{ fontSize: "0.88rem", color: "var(--text-primary)", margin: "0.3rem 0 1rem 0", lineHeight: 1.6 }}>
                {selectedAdvisory.body}
              </p>

              <div style={{ fontSize: "0.78rem", textTransform: "uppercase", color: "var(--text-muted)", fontWeight: 600 }}>
                Protective Recommended Actions ({selectedAdvisory.stakeholder})
              </div>
              <ul style={{ paddingLeft: "1.25rem", margin: "0.4rem 0 1rem 0", fontSize: "0.85rem", color: "#38bdf8" }}>
                {selectedAdvisory.actions.map((act, i) => (
                  <li key={i} style={{ marginBottom: "0.3rem", color: "var(--text-primary)" }}>
                    {act}
                  </li>
                ))}
              </ul>

              <div style={{ fontSize: "0.78rem", textTransform: "uppercase", color: "var(--text-muted)", fontWeight: 600 }}>
                Uncertainty & Confidence Communication
              </div>
              <p style={{ fontSize: "0.82rem", color: "var(--text-secondary)", fontStyle: "italic", margin: "0.25rem 0" }}>
                {selectedAdvisory.uncertainty_statement}
              </p>
            </div>

            {/* Deterministic Verifier Card */}
            <div
              className={`verifier-card ${selectedAdvisory.verification_passed ? "pass" : "fail"}`}
              style={{ marginBottom: "1.25rem" }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: "0.45rem", marginBottom: "0.4rem" }}>
                <ShieldCheck size={16} style={{ color: selectedAdvisory.verification_passed ? "#10b981" : "#ef4444" }} />
                <span style={{ fontSize: "0.82rem", fontWeight: 700, color: "#fff" }}>
                  IMD Deterministic Ground-Truth Verifier
                </span>
                <span style={{ fontSize: "0.72rem", color: "var(--text-muted)", marginLeft: "auto" }}>
                  Automated Check
                </span>
              </div>
              <div style={{ fontSize: "0.8rem", color: "var(--text-secondary)", display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.5rem" }}>
                <div>Ground Truth Severity: <strong>{selectedAdvisory.severity}</strong></div>
                <div>Ground Truth Temp: <strong>{selectedAdvisory.tmax_c}°C</strong></div>
                <div>Regenerations: <strong>{selectedAdvisory.regeneration_count}</strong></div>
                <div>Verification Pass: <strong>{selectedAdvisory.verification_passed ? "TRUE" : "FALSE"}</strong></div>
              </div>
            </div>

            {/* Review Comments / History */}
            {selectedAdvisory.reviewed_by && (
              <div style={{ background: "rgba(255, 255, 255, 0.03)", padding: "0.75rem", borderRadius: "8px", marginBottom: "1.25rem" }}>
                <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
                  Reviewed by: <strong>{selectedAdvisory.reviewed_by}</strong> on{" "}
                  {new Date(selectedAdvisory.reviewed_at || "").toLocaleString()}
                </div>
                {selectedAdvisory.review_comments && (
                  <div style={{ fontSize: "0.82rem", color: "#34d399", marginTop: "0.25rem" }}>
                    "{selectedAdvisory.review_comments}"
                  </div>
                )}
              </div>
            )}

            {/* Operator Review Controls */}
            {canReview ? (
              <div style={{ borderTop: "1px solid var(--border-subtle)", paddingTop: "1rem" }}>
                {selectedAdvisory.status === "PENDING_REVIEW" && (
                  <div>
                    <div className="form-group">
                      <label className="form-label">Review Verification Notes / Sign-Off Justification:</label>
                      <input
                        type="text"
                        className="form-input"
                        placeholder="e.g. Cross-verified with Nagpur AWS radar and local departure criteria."
                        value={reviewComment}
                        onChange={(e) => setReviewComment(e.target.value)}
                        id="review-comment-input"
                      />
                    </div>

                    <div style={{ display: "flex", gap: "0.75rem" }}>
                      <button
                        className="btn btn-success"
                        style={{ flex: 1 }}
                        onClick={handleApprove}
                        disabled={actionLoading}
                        id="approve-advisory-btn"
                      >
                        <CheckCircle2 size={16} /> Approve & Sign Advisory
                      </button>

                      <button
                        className="btn btn-danger"
                        onClick={() => setShowRejectModal(true)}
                        disabled={actionLoading}
                        id="reject-advisory-btn"
                      >
                        <XCircle size={16} /> Reject
                      </button>
                    </div>
                  </div>
                )}

                {selectedAdvisory.status === "APPROVED" && (
                  <div>
                    <button
                      className="btn btn-primary"
                      style={{ width: "100%" }}
                      onClick={handleDisseminate}
                      disabled={actionLoading}
                      id="disseminate-advisory-btn"
                    >
                      <Send size={16} /> Disseminate Early Warning (SMS & Multi-channel)
                    </button>
                  </div>
                )}

                {selectedAdvisory.status === "DISSEMINATED" && (
                  <div style={{ color: "#3b82f6", fontSize: "0.85rem", display: "flex", alignItems: "center", gap: "0.5rem" }}>
                    <CheckCircle2 size={16} /> Dissemination Complete at {new Date(selectedAdvisory.disseminated_at || "").toLocaleTimeString()}
                  </div>
                )}
              </div>
            ) : (
              <div style={{ fontSize: "0.8rem", color: "var(--text-muted)", fontStyle: "italic" }}>
                Current role '{currentRole}' has read-only access. Switch to Senior Meteorologist to approve or disseminate.
              </div>
            )}
          </div>
        )}
      </div>

      {/* Dissemination Details Modal */}
      {disseminationResult && (
        <div className="modal-overlay">
          <div className="modal-content">
            <h3 style={{ fontFamily: "var(--font-display)", color: "#fff", marginBottom: "0.75rem" }}>
              Advisory Disseminated Successfully
            </h3>
            <p style={{ fontSize: "0.85rem", color: "var(--text-secondary)", marginBottom: "1rem" }}>
              Advisory #{disseminationResult.advisory_id} signed off by {disseminationResult.authorized_by} has been exported for multi-channel transmission.
            </p>

            <div style={{ background: "rgba(0,0,0,0.4)", padding: "1rem", borderRadius: "8px", marginBottom: "1rem" }}>
              <div style={{ fontSize: "0.75rem", fontWeight: 700, color: "#38bdf8", marginBottom: "0.4rem" }}>
                PUBLIC SMS PAYLOAD (160 CHARS MAX):
              </div>
              <div className="font-mono" style={{ fontSize: "0.82rem", color: "#f8fafc" }}>
                {disseminationResult.channel_sms}
              </div>
            </div>

            <button className="btn btn-primary" onClick={() => setDisseminationResult(null)}>
              Close
            </button>
          </div>
        </div>
      )}

      {/* Reject Modal */}
      {showRejectModal && (
        <div className="modal-overlay">
          <div className="modal-content">
            <h3 style={{ fontFamily: "var(--font-display)", color: "#ef4444", marginBottom: "0.75rem" }}>
              Reject Heatwave Advisory
            </h3>
            <p style={{ fontSize: "0.85rem", color: "var(--text-secondary)", marginBottom: "1rem" }}>
              Provide mandatory meteorological justification for rejecting Advisory #{selectedAdvisory?.id}. This justification is cryptographically preserved in the audit log.
            </p>

            <div className="form-group">
              <label className="form-label">Meteorological Justification:</label>
              <textarea
                className="form-textarea"
                placeholder="e.g. Sea breeze arrived earlier than simulated, bringing coastal temperature down below 37C threshold."
                value={rejectReason}
                onChange={(e) => setRejectReason(e.target.value)}
                id="reject-reason-textarea"
              />
            </div>

            <div style={{ display: "flex", gap: "0.75rem", justifyContent: "flex-end" }}>
              <button className="btn btn-secondary" onClick={() => setShowRejectModal(false)}>
                Cancel
              </button>
              <button
                className="btn btn-danger"
                onClick={handleReject}
                disabled={!rejectReason.trim() || actionLoading}
                id="confirm-reject-btn"
              >
                Confirm Rejection
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
