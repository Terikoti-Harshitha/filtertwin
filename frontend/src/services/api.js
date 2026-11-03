/**
 * FilterTwin Frontend API Client.
 * Connects to the open-source FastAPI backend.
 */

const rawBase = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';
const API_BASE = rawBase.endsWith('/api/v1')
  ? rawBase
  : `${rawBase.replace(/\/+$/, '')}/api/v1`;

async function request(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`;
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {})
  };

  try {
    const response = await fetch(url, { ...options, headers });
    if (!response.ok) {
      const errData = await response.json().catch(() => ({}));
      throw new Error(errData.detail || `HTTP Error ${response.status}: ${response.statusText}`);
    }
    if (response.status === 204) return null;
    return await response.json();
  } catch (err) {
    console.error(`API Error on [${options.method || 'GET'}] ${url}:`, err);
    throw err;
  }
}

export const api = {
  // Purifiers
  getPurifiers: () => request('/purifiers'),
  getPurifier: (id) => request(`/purifiers/${id}`),
  createPurifier: (data) => request('/purifiers', { method: 'POST', body: JSON.stringify(data) }),
  updatePurifier: (id, data) => request(`/purifiers/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deletePurifier: (id) => request(`/purifiers/${id}`, { method: 'DELETE' }),

  // Simulations
  createSimulation: (data) => request('/simulations', { method: 'POST', body: JSON.stringify(data) }),
  getSimulation: (id) => request(`/simulations/${id}`),
  getReadings: (id, limit) => request(`/simulations/${id}/readings${limit ? `?limit=${limit}` : ''}`),
  injectFault: (id, data) => request(`/simulations/${id}/inject-fault`, { method: 'POST', body: JSON.stringify(data) }),
  pauseSimulation: (id) => request(`/simulations/${id}/pause`, { method: 'POST' }),
  resumeSimulation: (id) => request(`/simulations/${id}/resume`, { method: 'POST' }),
  resetSimulation: (id) => request(`/simulations/${id}/reset`, { method: 'POST' }),

  // Diagnostics
  predict: (simId) => request(`/diagnostics/${simId}/predict`, { method: 'POST' }),
  getLatestDiagnosis: (simId) => request(`/diagnostics/${simId}/latest`),
  getAlerts: (simId) => request(`/diagnostics/${simId}/alerts`),

  // Evaluations
  getLatestEvaluation: () => request('/evaluations/latest'),
  triggerEvaluation: (data = { num_scenarios: 200, include_faults: true }) =>
    request('/evaluations', { method: 'POST', body: JSON.stringify(data) }),
  getReportCsvUrl: () => `${API_BASE}/evaluations/report/csv`,

  // Maintenance
  getGuides: () => request('/maintenance/guides'),
  getGuide: (id) => request(`/maintenance/guides/${id}`),
  recordMaintenance: (data) => request('/maintenance/records', { method: 'POST', body: JSON.stringify(data) }),
  getMaintenanceHistory: (purifierId) =>
    request(`/maintenance/records${purifierId ? `?purifier_id=${purifierId}` : ''}`),

  // Models
  getModels: () => request('/models'),

  // IoT Telemetry Ingestion (Wokwi / Hardware ESP32)
  ingestTelemetry: (data) => request('/simulations/telemetry/ingest', { method: 'POST', body: JSON.stringify(data) }),
};

export default api;
