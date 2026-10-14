import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request Interceptor: Attach JWT bearer token if available
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('ildo_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response Interceptor: Standardize error extraction and handle expired sessions
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid
      const isAuthRequest = error.config?.url?.includes('/auth/login');
      if (!isAuthRequest) {
        localStorage.removeItem('ildo_token');
        localStorage.removeItem('ildo_user');
      }
    }
    
    // Normalize human-readable error message
    const message =
      error.response?.data?.message ||
      error.response?.data?.detail ||
      error.message ||
      'An unexpected network error occurred';

    error.normalizedMessage = message;
    return Promise.reject(error);
  }
);

// System health API calls
export const getSystemHealth = async () => {
  const response = await apiClient.get('/api/v1/health');
  return response.data;
};

export const pingBackend = async () => {
  const response = await apiClient.get('/api/v1/health/ping');
  return response.data;
};
