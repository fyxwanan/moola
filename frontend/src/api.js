import axios from 'axios';

const getBaseURL = () => {
  const isElectron = typeof window !== 'undefined' && window.navigator && window.navigator.userAgent.toLowerCase().includes('electron');
  const isCapacitor = typeof window !== 'undefined' && (window.Capacitor || window.location.href.startsWith('capacitor://') || window.location.href.startsWith('http://localhost'));
  const isProd = import.meta.env.PROD;

  if (import.meta.env.VITE_API_BASE_URL) {
    return import.meta.env.VITE_API_BASE_URL;
  }

  if (isElectron || isCapacitor || isProd) {
    return 'http://192.168.147.4';
  }

  const hostname = window.location.hostname || '127.0.0.1';
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
      const isElectron = typeof window !== 'undefined' && window.navigator && window.navigator.userAgent.toLowerCase().includes('electron');
      const isCapacitor = typeof window !== 'undefined' && (window.Capacitor || window.location.href.startsWith('capacitor://') || window.location.href.startsWith('http://localhost'));
      const isHashRouting = isElectron || isCapacitor;
      
      const currentPath = isHashRouting ? window.location.hash : window.location.pathname;
      const isLoginOrAuth = isHashRouting 
        ? (currentPath.startsWith('#/login') || currentPath.startsWith('#/auth'))
        : (currentPath === '/login' || currentPath === '/auth');
        
      if (!isLoginOrAuth) {
        localStorage.removeItem('moola_token');
        localStorage.removeItem('moola_user');
        if (isHashRouting) {
          window.location.hash = '#/login';
        } else {
          window.location.href = '/login';
        }
      }
    }
    return Promise.reject(error);
  }
);

export default api;
