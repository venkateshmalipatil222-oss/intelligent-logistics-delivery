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
      const isAuthRequest = error.config?.url?.includes('/auth/login');
      if (!isAuthRequest) {
        localStorage.removeItem('ildo_token');
        localStorage.removeItem('ildo_user');
      }
    }

    const message =
      error.response?.data?.message ||
      error.response?.data?.detail ||
      error.message ||
      'An unexpected network error occurred';

    error.normalizedMessage = message;
    return Promise.reject(error);
  }
);

// ============================================================================
// System & Health API
// ============================================================================
export const getSystemHealth = async () => {
  const response = await apiClient.get('/api/v1/health');
  return response.data;
};

export const pingBackend = async () => {
  const response = await apiClient.get('/api/v1/health/ping');
  return response.data;
};

// ============================================================================
// Auth & User API
// ============================================================================
export const loginUser = async (credentials) => {
  const response = await apiClient.post('/api/v1/auth/login', credentials);
  return response.data;
};

export const registerUser = async (userData) => {
  const response = await apiClient.post('/api/v1/auth/register', userData);
  return response.data;
};

export const getCurrentUser = async () => {
  const response = await apiClient.get('/api/v1/auth/me');
  return response.data;
};

export const listUsers = async (params = {}) => {
  const response = await apiClient.get('/api/v1/users', { params });
  return response.data;
};

// ============================================================================
// Warehouse API
// ============================================================================
export const listWarehouses = async (params = {}) => {
  const response = await apiClient.get('/api/v1/warehouses', { params });
  return response.data;
};

export const getWarehouse = async (id) => {
  const response = await apiClient.get(`/api/v1/warehouses/${id}`);
  return response.data;
};

export const createWarehouse = async (warehouseData) => {
  const response = await apiClient.post('/api/v1/warehouses', warehouseData);
  return response.data;
};

export const updateWarehouse = async (id, updateData) => {
  const response = await apiClient.put(`/api/v1/warehouses/${id}`, updateData);
  return response.data;
};

// ============================================================================
// Fleet & Vehicle API
// ============================================================================
export const listVehicles = async (params = {}) => {
  const response = await apiClient.get('/api/v1/vehicles', { params });
  return response.data;
};

export const getVehicle = async (id) => {
  const response = await apiClient.get(`/api/v1/vehicles/${id}`);
  return response.data;
};

export const createVehicle = async (vehicleData) => {
  const response = await apiClient.post('/api/v1/vehicles', vehicleData);
  return response.data;
};

export const updateVehicle = async (id, updateData) => {
  const response = await apiClient.put(`/api/v1/vehicles/${id}`, updateData);
  return response.data;
};

// ============================================================================
// Driver Operations API
// ============================================================================
export const listDrivers = async (params = {}) => {
  const response = await apiClient.get('/api/v1/drivers', { params });
  return response.data;
};

export const getDriverMe = async () => {
  const response = await apiClient.get('/api/v1/drivers/me');
  return response.data;
};

export const getDriver = async (id) => {
  const response = await apiClient.get(`/api/v1/drivers/${id}`);
  return response.data;
};

export const createDriver = async (driverData) => {
  const response = await apiClient.post('/api/v1/drivers', driverData);
  return response.data;
};

export const updateDriver = async (id, updateData) => {
  const response = await apiClient.put(`/api/v1/drivers/${id}`, updateData);
  return response.data;
};

export const updateDriverLocation = async (coords) => {
  const response = await apiClient.post('/api/v1/drivers/location', coords);
  return response.data;
};

// ============================================================================
// Order Pipeline API
// ============================================================================
export const listOrders = async (params = {}) => {
  const response = await apiClient.get('/api/v1/orders', { params });
  return response.data;
};

export const getOrder = async (id) => {
  const response = await apiClient.get(`/api/v1/orders/${id}`);
  return response.data;
};

export const createOrder = async (orderData) => {
  const response = await apiClient.post('/api/v1/orders', orderData);
  return response.data;
};

export const updateOrderStatus = async (id, statusData) => {
  const response = await apiClient.put(`/api/v1/orders/${id}/status`, statusData);
  return response.data;
};

export const trackShipment = async (trackingOrOrderNumber) => {
  const response = await apiClient.get(`/api/v1/orders/track/${encodeURIComponent(trackingOrOrderNumber)}`);
  return response.data;
};

// ============================================================================
// Delivery Dispatch & State Machine API
// ============================================================================
export const dispatchOrder = async (dispatchData) => {
  const response = await apiClient.post('/api/v1/deliveries/dispatch', dispatchData);
  return response.data;
};

export const listDeliveries = async (params = {}) => {
  const response = await apiClient.get('/api/v1/deliveries', { params });
  return response.data;
};

export const getDelivery = async (id) => {
  const response = await apiClient.get(`/api/v1/deliveries/${id}`);
  return response.data;
};

export const transitionDeliveryStatus = async (id, transitionData) => {
  const response = await apiClient.post(`/api/v1/deliveries/${id}/status`, transitionData);
  return response.data;
};

export const verifyDeliveryOTP = async (id, otpData) => {
  const response = await apiClient.post(`/api/v1/deliveries/${id}/verify-otp`, otpData);
  return response.data;
};

// ============================================================================
// Intelligent Decision & Optimization Engines API
// ============================================================================
export const recommendDriverForOrder = async (orderId) => {
  const response = await apiClient.get(`/api/v1/intelligence/recommend-driver/${orderId}`);
  return response.data;
};

export const autoAssignDriver = async (orderId) => {
  const response = await apiClient.post(`/api/v1/intelligence/auto-assign/${orderId}`);
  return response.data;
};

export const optimizeRoute = async (routeData) => {
  const response = await apiClient.post('/api/v1/intelligence/optimize-route', routeData);
  return response.data;
};

export const optimizeMultiStop = async (multiStopData) => {
  const response = await apiClient.post('/api/v1/intelligence/optimize-multi-stop', multiStopData);
  return response.data;
};

export const estimateCost = async (costParams) => {
  const response = await apiClient.post('/api/v1/intelligence/estimate-cost', costParams);
  return response.data;
};
