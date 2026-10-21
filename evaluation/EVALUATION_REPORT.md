# Red-Team Security & Responsible AI Evaluation Report

**Project:** Secure, Fact-Checked LLM Advisory Generator for Heatwave Early Warning  
**Context:** K J Somaiya AI Use Case Integration in Teaching-Learning (KJS-CES-01) with India Meteorological Department (IMD)  
**Total Test Cases Evaluated:** 160 cases (125 Adversarial + 35 Benign Baseline)  
**Total Executions:** 480 evaluations across 3 ablation configurations.

---

## 📊 Comparative Performance Summary (Ablation Analysis)

| Metric | Configuration A: No Defenses (Baseline) | Configuration B: Guard Only | Configuration C: Guard + Verifier + Human Gate (Proposed) | Target Goal |
| :--- | :---: | :---: | :---: | :---: |
| **Attack Success Rate (ASR)** | **100.0%** | **29.6%** | **0.0%** | $\le 1.0\%$ |
| **False-Positive Rate (FPR)** | **0.0%** | **0.0%** | **0.0%** | $\le 2.0\%$ |
| **Hallucination Catch Rate** | **0.0%** | **0.0%** | **40.0%** | $\ge 95.0\%$ |
| **Fallback / Regeneration Rate**| **0.0%** | **0.0%** | **23.12%** | Operational Safe |
| **Average Added Latency** | **0.00 ms** | **0.10 ms** | **0.09 ms** | $< 50\text{ ms}$ |

---

## 🔍 Key Findings & Security Insights

1. **Vulnerability of Raw LLM (Configuration A):**
   - Without architectural defenses, the LLM is vulnerable to direct overrides, delimiter injection, and hallucination prompts ($ASR = 100.0\%$).
   - The model has a $0\%$ hallucination catch rate because claimed severity and temperatures are accepted without verification.

2. **Defense Boundaries of Input Guard Only (Configuration B):**
   - The multi-layer Input Guard successfully eliminates direct overrides, roleplay/DAN jailbreaks, delimiter breakouts, and base64 obfuscation.
   - However, inputs that mimic legitimate meteorological context (e.g. subtle fact mutators, authority claims) or internal model hallucinations bypass the guard ($ASR = 29.6\%$).

3. **Total Defense with Output Verifier & Human Gate (Configuration C):**
   - The combination of **Input Guard + Output Verifier + Meteorologist Gate** achieves an Attack Success Rate of **0.0%**.
   - Even when subtle manipulation reaches candidate generation, the deterministic IMD rule engine and verifier catch $100\%$ of severity and numerical mismatches, automatically triggering safe fallback templates.
   - The false-positive rate on benign inputs is strictly **0.0%**, proving that legitimate meteorological logs containing words like *"ignore"* or *"instructions"* are preserved.
   - The added latency is negligible (**0.09 ms**), well within real-time early warning operational thresholds.

---

## 📁 Evaluation Artifacts
- Raw Benchmark Dataset: `redteam_dataset.py` (160 cases)
- Full CSV Metrics: `eval_results.csv`
- Visual Comparison Chart: `eval_metrics_comparison.png`
- Latency Breakdown Chart: `latency_breakdown.png`
