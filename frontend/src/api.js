import axios from 'axios';

const getBaseURL = () => {
  if (import.meta.env.VITE_API_BASE_URL && !import.meta.env.VITE_API_BASE_URL.includes('localhost')) {
    return import.meta.env.VITE_API_BASE_URL;
  }
  if (import.meta.env.PROD) {
    return '';
  }
  const hostname = window.location.hostname;
  return `http://${hostname}:8000`;
};

const api = axios.create({
  baseURL: `${getBaseURL()}/api`,
  timeout: 10000,
});

// Request interceptor to attach JWT token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('moola_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to check for refreshed token in headers
api.interceptors.response.use(
  (response) => {
    // If the backend sent a refreshed token, extract and save it
    const refreshedToken = response.headers['authorization'];
    if (refreshedToken && refreshedToken.startsWith('Bearer ')) {
      const token = refreshedToken.substring(7);
      localStorage.setItem('moola_token', token);
      
      // Update global auth store if initialized
      window.dispatchEvent(new CustomEvent('moola-token-refreshed', { detail: token }));
    }
    return response;
  },
  (error) => {
    if (error.response && error.response.status === 401) {
      // Clear token and redirect to login if not already on the login page
      const currentPath = window.location.pathname;
      if (currentPath !== '/login' && currentPath !== '/auth') {
        localStorage.removeItem('moola_token');
        localStorage.removeItem('moola_user');
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export default api;
