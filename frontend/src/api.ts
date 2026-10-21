/**
 * Unified API Client for IMD-CES Heatwave Early Warning Platform
 */

const API_BASE = "/api/v1";

let authToken: string | null = localStorage.getItem("imd_auth_token");

export function setAuthToken(token: string | null) {
  authToken = token;
  if (token) {
    localStorage.setItem("imd_auth_token", token);
  } else {
    localStorage.removeItem("imd_auth_token");
  }
}

export function getAuthToken(): string | null {
  return authToken || localStorage.getItem("imd_auth_token");
}

async function fetchWithAuth(endpoint: string, options: RequestInit = {}) {
  const headers = new Headers(options.headers || {});
  headers.set("Content-Type", "application/json");

  const token = getAuthToken();
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let errorDetail = `Request failed with status ${response.status}`;
    try {
      const errorJson = await response.json();
      errorDetail = errorJson.detail || JSON.stringify(errorJson);
    } catch {
      // fallback
    }
    throw new Error(errorDetail);
  }

  return response.json();
}

// System Health
export async function getSystemHealth() {
  return fetchWithAuth("/health");
}

export async function getLLMHealth() {
  return fetchWithAuth("/health/llm");
}

// Authentication
export async function loginUser(username: string, password: string) {
  const data = await fetchWithAuth("/auth/login", {
    method: "POST",
    body: JSON.stringify({ username, password }),
  });
  if (data.access_token) {
    setAuthToken(data.access_token);
  }
  return data;
}

export async function getCurrentUser() {
  return fetchWithAuth("/auth/me");
}

// Forecasts
export async function listForecasts(params: Record<string, any> = {}) {
  const q = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== null && v !== "") {
      q.append(k, String(v));
    }
  }
  return fetchWithAuth(`/forecasts?${q.toString()}`);
}

export async function createForecast(payload: any) {
  return fetchWithAuth("/forecasts", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function evaluateRuleEngine(payload: {
  region_type: string;
  forecast_tmax_c: number;
  normal_tmax_c: number;
}) {
  return fetchWithAuth("/forecasts/evaluate", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

// Advisories
export async function listAdvisories(params: Record<string, any> = {}) {
  const q = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== null && v !== "") {
      q.append(k, String(v));
    }
  }
  return fetchWithAuth(`/advisories?${q.toString()}`);
}

export async function getAdvisory(id: number) {
  return fetchWithAuth(`/advisories/${id}`);
}

export async function generateAdvisory(payload: any) {
  return fetchWithAuth("/advisories/generate", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function approveAdvisory(id: number, comments?: string) {
  return fetchWithAuth(`/advisories/${id}/approve`, {
    method: "POST",
    body: JSON.stringify({ comments: comments || "Approved by duty meteorologist" }),
  });
}

export async function rejectAdvisory(id: number, reason: string) {
  return fetchWithAuth(`/advisories/${id}/reject`, {
    method: "POST",
    body: JSON.stringify({ reason }),
  });
}

export async function disseminateAdvisory(id: number) {
  return fetchWithAuth(`/advisories/${id}/disseminate`, {
    method: "POST",
  });
}

// Security Input Guard
export async function checkInputSecurity(text: string, source: string = "operator_notes") {
  return fetchWithAuth("/guard/check", {
    method: "POST",
    body: JSON.stringify({ text, source }),
  });
}

// Audit & Metrics
export async function getAuditTrail(params: Record<string, any> = {}) {
  const q = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== null && v !== "") {
      q.append(k, String(v));
    }
  }
  return fetchWithAuth(`/audit?${q.toString()}`);
}

export async function verifyAuditChain() {
  return fetchWithAuth("/audit/verify");
}

export async function getOperationalMetrics() {
  return fetchWithAuth("/metrics");
}
