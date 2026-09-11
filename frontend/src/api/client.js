import axios from 'axios';

/**
 * Client HTTP partagé par toute l'application. `withCredentials: true` est
 * indispensable pour que le navigateur transmette le cookie HttpOnly contenant
 * le JWT (voir Mission 13) lors de chaque requête vers l'API.
 */
const api = axios.create({
  // En local (proxy Vite) : baseURL relative '/api'. En ligne, si le frontend
  // et le backend sont sur des domaines différents, définissez VITE_API_URL
  // (ex. https://mon-backend.onrender.com/api) dans un .env du frontend.
  baseURL: import.meta.env.VITE_API_URL || '/api',
  withCredentials: true,
});

export const authApi = {
  register: (email, password) => api.post('/auth/register', { email, password }),
  login: (email, password) => api.post('/auth/login', { email, password }),
  logout: () => api.post('/auth/logout'),
  me: () => api.get('/auth/me'),
};

export const botApi = {
  getTrades: (limit = 200) => api.get('/bot/trades', { params: { limit } }),
  getLogs: (limit = 100) => api.get('/bot/logs', { params: { limit } }),
  getStatus: () => api.get('/bot/status'),
  getPerformance: () => api.get('/bot/performance'),
  getSnapshots: (limit = 300) => api.get('/bot/snapshots', { params: { limit } }),
  getConfig: () => api.get('/bot/config'),
  setManualOverride: (paused, reason = '') => api.post('/bot/config/override', { paused, reason }),
  startProcess: () => api.post('/bot/process/start'),
  stopProcess: () => api.post('/bot/process/stop'),
  getProcessStatus: () => api.get('/bot/process/status'),
};

export default api;
