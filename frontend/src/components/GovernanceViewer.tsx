import React, { useState } from "react";
import {
  ShieldAlert,
  FileText,
  Scale,
  Award,
  CheckCircle2,
  Lock,
  Eye,
  AlertTriangle,
} from "lucide-react";

export const GovernanceViewer: React.FC = () => {
  const [activeSubTab, setActiveSubTab] = useState<"stride" | "dpdp" | "responsible_ai">("stride");

  const STRIDE_ITEMS = [
    {
      category: "S - Spoofing",
      threat: "Rogue operator or malicious client injecting unauthorized forecasts or forging senior meteorologist signature.",
      impact: "HIGH",
      mitigation: "JWT Bearer authentication (HMAC-SHA256), strict role enforcement (viewer, meteorologist, admin), digitally signed approval logs.",
      status: "VERIFIED",
    },
    {
      category: "T - Tampering",
      threat: "Altering observed temperature records, injecting adversarial directives in notes, or retroactively editing audit logs.",
      impact: "CRITICAL",
      mitigation: "Multi-tier Input Guard (Unicode NFKC, homoglyphs, regex), Deterministic Output Verifier against IMD ground truth, SHA-256 hash-chaining.",
      status: "VERIFIED",
    },
    {
      category: "R - Repudiation",
      threat: "Operator or approver denying having authorized or rejected an early warning advisory during post-disaster accountability audits.",
      impact: "HIGH",
      mitigation: "Append-only SHA-256 hash-chained audit ledger capturing actor username, role, timestamp, and immutable state diffs.",
      status: "VERIFIED",
    },
    {
      category: "I - Information Disclosure",
      threat: "Prompt extraction attacks leaking proprietary IMD instructions, internal canary secrets, or infrastructure credentials.",
      impact: "HIGH",
      mitigation: "Ephemeral canary tokens (CANARY-IMD-SEC-XXXX), verifier check ensuring zero canary leakage, environment secret isolation.",
      status: "VERIFIED",
    },
    {
      category: "D - Denial of Service",
      threat: "ReDoS catastrophic backtracking via malicious regex strings, or infinite hallucination loops consuming LLM budgets.",
      impact: "MEDIUM",
      mitigation: "Precompiled non-backtracking regex with character length caps, bounded regeneration budget (max_retries=2), instant safe template fallback.",
      status: "VERIFIED",
    },
    {
      category: "E - Elevation of Privilege",
      threat: "Read-only viewer or unauthenticated actor attempting to approve or trigger mass early warning dissemination.",
      impact: "CRITICAL",
      mitigation: "FastAPI require_role dependency guards on all mutation endpoints; strict state machine transitions (DRAFT -> PENDING_REVIEW -> APPROVED -> DISSEMINATED).",
      status: "VERIFIED",
    },
  ];

  const DPDP_ITEMS = [
    {
      section: "Section 4: Grounds for Processing",
      mandate: "Personal data shall be processed only for lawful purposes with notice or legitimate use.",
      compliance: "Zero citizen PII is collected or stored. Operator logins use institutional identifiers (@imd.gov.in) strictly for meteorological duty logging.",
      status: "COMPLIANT",
    },
    {
      section: "Section 7(d): Legitimate Uses (Disaster & Public Health)",
      mandate: "Processing without consent for responding to medical emergencies, disasters, or breakdown of public order.",
      compliance: "Heatwave early warning dissemination falls squarely under Section 7(d) disaster emergency management mandates coordinated with NDMA.",
      status: "COMPLIANT",
    },
    {
      section: "Section 8(4): Data Accuracy",
      mandate: "Ensuring accuracy and completeness of data that influences decisions or disclosures.",
      compliance: "Deterministic rule engine anchors all advisories to official IMD numerical thresholds; hallucinated temperatures are strictly rejected.",
      status: "COMPLIANT",
    },
    {
      section: "Section 8(5): Reasonable Security Safeguards",
      mandate: "Technical and organizational measures to prevent personal data breaches.",
      compliance: "Cryptographic SHA-256 hash chains, input sanitization, multi-layer injection guard, and role-based access control.",
      status: "COMPLIANT",
    },
    {
      section: "Section 8(6): Breach Notification & Audit",
      mandate: "Timely notification to the Data Protection Board of India and affected principals.",
      compliance: "Automated hash chain validation (/api/v1/audit/verify) alerts administrators immediately if any historical log discontinuity occurs.",
      status: "COMPLIANT",
    },
  ];

  const RESPONSIBLE_AI_PRINCIPLES = [
    {
      title: "1. Safety & Reliability",
      desc: "Architectural guardrails guarantee no hallucinated or unverified weather severity alert reaches the public, backed by safe deterministic fallback templates.",
    },
    {
      title: "2. Equality & Inclusivity",
      desc: "Multilingual advisory generation in English, Hindi, and Marathi ensures alerts reach vulnerable rural farmers and non-English-speaking laborers.",
    },
    {
      title: "3. Transparency & Explainability",
      desc: "Every generated advisory explicitly documents its meteorological rationale, departure from normal, and confidence level.",
    },
    {
      title: "4. Human Accountability",
      desc: "Certified meteorologists retain mandatory review and sign-off authority prior to mass multi-channel early warning broadcast.",
    },
    {
      title: "5. Data Minimization & Privacy",
      desc: "Strictly numerical weather forecasts and institutional operator credentials are used; zero citizen tracking or location tracking.",
    },
  ];

  return (
    <div className="tab-pane" id="governance-viewer">
      <div className="section-header">
        <div className="section-title-wrap">
          <h2 className="section-title">
            <Scale style={{ color: "#38bdf8" }} />
            Phase 7: System Hardening, Threat Modeling & DPDP Act 2023 Compliance
          </h2>
          <p className="section-desc">
            Statutory and security engineering frameworks aligning with Indian Meteorological Standards, DPDP Act 2023, and NITI Aayog AI Ethics.
          </p>
        </div>
      </div>

      {/* Subtab Toggle */}
      <div style={{ display: "flex", gap: "0.5rem", marginBottom: "1.25rem" }}>
        <button
          className={`btn btn-sm ${activeSubTab === "stride" ? "btn-primary" : "btn-secondary"}`}
          onClick={() => setActiveSubTab("stride")}
        >
          <ShieldAlert size={14} /> STRIDE Threat Model
        </button>
        <button
          className={`btn btn-sm ${activeSubTab === "dpdp" ? "btn-primary" : "btn-secondary"}`}
          onClick={() => setActiveSubTab("dpdp")}
        >
          <Scale size={14} /> DPDP Act 2023 Compliance Matrix
        </button>
        <button
          className={`btn btn-sm ${activeSubTab === "responsible_ai" ? "btn-primary" : "btn-secondary"}`}
          onClick={() => setActiveSubTab("responsible_ai")}
        >
          <Award size={14} /> NITI Aayog Responsible AI
        </button>
      </div>

      {/* STRIDE Tab */}
      {activeSubTab === "stride" && (
        <div className="glass-panel" style={{ padding: "1.5rem" }}>
          <h3 style={{ fontFamily: "var(--font-display)", color: "#fff", fontSize: "1.1rem", marginBottom: "0.5rem" }}>
            Microsoft STRIDE Threat Analysis & Defense Mapping
          </h3>
          <p style={{ fontSize: "0.82rem", color: "var(--text-muted)", marginBottom: "1.25rem" }}>
            Comprehensive vulnerability surface assessment and verified architectural countermeasures.
          </p>

          <div className="table-responsive">
            <table className="custom-table">
              <thead>
                <tr>
                  <th>STRIDE Category</th>
                  <th>Threat Vector</th>
                  <th>Impact</th>
                  <th>Architectural Mitigation</th>
                  <th>Verification</th>
                </tr>
              </thead>
              <tbody>
                {STRIDE_ITEMS.map((item, idx) => (
                  <tr key={idx}>
                    <td style={{ fontWeight: 700, color: "#38bdf8", whiteSpace: "nowrap" }}>
                      {item.category}
                    </td>
                    <td style={{ fontSize: "0.82rem", maxWidth: "260px" }}>{item.threat}</td>
                    <td>
                      <span
                        style={{
                          fontSize: "0.72rem",
                          padding: "0.2rem 0.5rem",
                          borderRadius: "4px",
                          background: item.impact === "CRITICAL" ? "rgba(239, 68, 68, 0.2)" : "rgba(245, 158, 11, 0.2)",
                          color: item.impact === "CRITICAL" ? "#ef4444" : "#f59e0b",
                          fontWeight: 700,
                        }}
                      >
                        {item.impact}
                      </span>
                    </td>
                    <td style={{ fontSize: "0.82rem", maxWidth: "340px", color: "var(--text-secondary)" }}>
                      {item.mitigation}
                    </td>
                    <td>
                      <span className="status-badge APPROVED" style={{ fontSize: "0.7rem" }}>
                        <CheckCircle2 size={12} style={{ marginRight: "3px" }} /> {item.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* DPDP Act 2023 Tab */}
      {activeSubTab === "dpdp" && (
        <div className="glass-panel" style={{ padding: "1.5rem" }}>
          <h3 style={{ fontFamily: "var(--font-display)", color: "#fff", fontSize: "1.1rem", marginBottom: "0.5rem" }}>
            Digital Personal Data Protection Act, 2023 (India) Compliance Matrix
          </h3>
          <p style={{ fontSize: "0.82rem", color: "var(--text-muted)", marginBottom: "1.25rem" }}>
            Statutory obligations under DPDP 2023 and mission-critical public safety exemptions.
          </p>

          <div className="table-responsive">
            <table className="custom-table">
              <thead>
                <tr>
                  <th>DPDP Provision</th>
                  <th>Statutory Mandate</th>
                  <th>System Safeguard & Implementation</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {DPDP_ITEMS.map((item, idx) => (
                  <tr key={idx}>
                    <td style={{ fontWeight: 700, color: "#38bdf8", whiteSpace: "nowrap" }}>
                      {item.section}
                    </td>
                    <td style={{ fontSize: "0.82rem", maxWidth: "240px" }}>{item.mandate}</td>
                    <td style={{ fontSize: "0.82rem", maxWidth: "360px", color: "var(--text-secondary)" }}>
                      {item.compliance}
                    </td>
                    <td>
                      <span className="status-badge APPROVED" style={{ fontSize: "0.7rem" }}>
                        <CheckCircle2 size={12} style={{ marginRight: "3px" }} /> {item.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Responsible AI Tab */}
      {activeSubTab === "responsible_ai" && (
        <div className="glass-panel" style={{ padding: "1.5rem" }}>
          <h3 style={{ fontFamily: "var(--font-display)", color: "#fff", fontSize: "1.1rem", marginBottom: "0.5rem" }}>
            NITI Aayog National Strategy for Artificial Intelligence: 7 Principles Alignment
          </h3>
          <p style={{ fontSize: "0.82rem", color: "var(--text-muted)", marginBottom: "1.25rem" }}>
            Ethical and operational design standards for responsible public sector AI deployments.
          </p>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))", gap: "1rem" }}>
            {RESPONSIBLE_AI_PRINCIPLES.map((p, idx) => (
              <div
                key={idx}
                style={{
                  background: "rgba(255, 255, 255, 0.03)",
                  border: "1px solid var(--border-subtle)",
                  borderRadius: "10px",
                  padding: "1.15rem",
                }}
              >
                <div style={{ fontWeight: 700, color: "#38bdf8", marginBottom: "0.4rem", fontSize: "0.95rem" }}>
                  {p.title}
                </div>
                <div style={{ fontSize: "0.82rem", color: "var(--text-secondary)", lineHeight: 1.5 }}>
                  {p.desc}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
