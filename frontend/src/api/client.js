import axios from 'axios';

/**
 * Client HTTP partagé par toute l'application. `withCredentials: true` est
 * indispensable pour que le navigateur transmette le cookie HttpOnly contenant
 * le JWT (voir Mission 13) lors de chaque requête vers l'API.
 */
const api = axios.create({
  baseURL: '/api',
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
};

export default api;
