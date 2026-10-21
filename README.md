# Secure, Fact-Checked LLM Advisory Generator for Heatwave Early Warning

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green.svg)](https://fastapi.tiangolo.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An academic & research-grade AI advisory generation platform developed under the K J Somaiya **"AI Use Case Integration in Teaching-Learning" (KJS-CES-01: Climate, Energy & Sustainability)** initiative with the **India Meteorological Department (IMD)**.

This system provides a trustworthy, deterministic, human-gated LLM advisory layer that ingests numerical/spatial weather forecasts, defends against adversarial prompt injections, deterministically verifies outputs against official IMD meteorological criteria, and enforces mandatory meteorologist sign-off prior to dissemination.

---

## 🏗️ Architecture Overview

```
 [ Weather Forecast Input (IMD / AWS / Synthetic) ]
                         │
                         ▼
             [ 1. Forecast Service ]
             (Deterministic Severity Engine)
                         │
        ┌────────────────┴────────────────┐
        ▼                                 ▼
[ Operator / Free-text Notes ]    [ Structured Forecast Data ]
        │                                 │
        ▼                                 │
  [ 2. Input Guard ]                      │
  (Unicode / Regex / Canary)              │
        │ (Sanitized / Checked)           │
        └────────────────┬────────────────┘
                         ▼
            [ 3. Advisory Generator ]
            (Prompt Synthesis: Citizen/Farmer/Disaster)
                         │
                         ▼
               [ LLM Provider Layer ]
         (Offline MockLLM / OpenAI / Anthropic)
                         │
                         ▼
            [ 4. Output Verifier ] ◄── (IMD Ground-Truth Rules)
          - Schema & Numeric Tolerances
          - Strict Severity Matching
          - Safety & Action Whitelist
          - Canary Exfiltration Check
                         │
         ┌───────────────┴───────────────┐
      [PASS]                          [FAIL]
         │                               │
         │                        [Auto-Regenerate x N]
         │                               │ (if failed)
         │                        [Safe Template Fallback]
         ▼                               ▼
       [ 5. Human-in-the-Loop Review Queue ]
       (Meteorologist Verification & Sign-off)
                         │
                         ▼
        [ 6. Tamper-Evident Audit Log ]
           (SHA-256 Hash Chaining)
                         │
                         ▼
       [ 7. Dissemination Stub (SMS/JSON) ]
```

---

## 🚀 Quickstart & Verification (Phase 0)

### 1. Prerequisites
- Python 3.11+
- Git
- Docker & Docker Compose (optional for containerized run)

### 2. Environment Setup
```bash
cd backend
python -m venv venv

# Windows
.\venv\Scripts\activate

# Linux / macOS
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Run the Backend Server
```bash
uvicorn app.main:app --reload --port 8000
```
- Interactive API Docs: [http://localhost:8000/api/v1/docs](http://localhost:8000/api/v1/docs)
- Health Check: [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)
- LLM Connection Test: [http://localhost:8000/api/v1/health/llm](http://localhost:8000/api/v1/health/llm)

### 4. Run Test Suite
```bash
pytest -v
```

### 5. Run Red-Team Evaluation Benchmark (Phase 5)
```bash
# From backend directory
python -m app.evaluation.run_eval
```

### 6. Run Frontend Dashboard (Phase 6)
```bash
cd ../frontend
npm install
npm run dev
```
- Frontend UI: [http://localhost:3000](http://localhost:3000)

### 7. Run E2E Demonstration Scenarios (Phase 7)
```bash
# From workspace root
.\backend\venv\Scripts\python.exe scripts/demo_scenarios.py
```

### 8. Run Full Stack via Docker Compose
```bash
docker-compose up --build
```

---

## 🧪 Implementation Roadmap

- [x] **Phase 0: Scaffold & Architecture** (Repo structure, config, deterministic MockLLMClient, Docker, CI pytest setup)
- [x] **Phase 1: Domain Core & IMD Rule Engine** (Plains/Hilly/Coastal criteria, synthetic forecast seeder, boundary tests)
- [x] **Phase 2: Structured Advisory Generation** (Multi-stakeholder templates, multilingual prompts, mock LLM pipeline)
- [x] **Phase 3: Multi-Layer Input Security Guard** (Unicode normalizer, injection regex, canary detection, test suites)
- [x] **Phase 4: Output Verifier & Human Approval Workflow** (Ground-truth verifier, fallback, RBAC, hash-chained audit log)
- [x] **Phase 5: Automated Red-Team Evaluation Harness** (160 attack benchmarks, A/B/C ablation analysis, CSV + Markdown + Matplotlib metrics)
- [x] **Phase 6: Frontend Dashboard** (React, Vite, TypeScript, Recharts, Reviewer Portal, Live Simulator, Security Sandbox)
- [x] **Phase 7: System Hardening & Documentation** (STRIDE threat model, DPDP Act 2023 compliance matrix, 5 E2E demo scenarios)

---

## 📚 Security & Compliance Documentation
- [STRIDE Threat Model](docs/STRIDE_THREAT_MODEL.md)
- [DPDP Act 2023 & Responsible AI Compliance Matrix](docs/COMPLIANCE_DPDP_ACT_2023.md)
- [Red-Team Benchmark Evaluation Report](backend/app/evaluation/reports/EVALUATION_REPORT.md)

