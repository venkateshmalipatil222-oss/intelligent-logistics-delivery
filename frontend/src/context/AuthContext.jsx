import React, { createContext, useContext, useState, useEffect } from 'react';
import { apiClient } from '../api/client';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem('ildo_user');
    return saved ? JSON.parse(saved) : null;
  });
  const [token, setToken] = useState(() => localStorage.getItem('ildo_token'));
  const [loading, setLoading] = useState(true);

  // Sync token state and verify session on initial load
  useEffect(() => {
    const verifySession = async () => {
      const storedToken = localStorage.getItem('ildo_token');
      if (storedToken) {
        try {
          const response = await apiClient.get('/api/v1/auth/me');
          setUser(response.data);
          localStorage.setItem('ildo_user', JSON.stringify(response.data));
        } catch (err) {
          // Token expired or invalid
          logout();
        }
      }
      setLoading(false);
    };

    verifySession();
  }, []);

  const login = async (email, password) => {
    const response = await apiClient.post('/api/v1/auth/login', {
      email,
      password,
    });
    const data = response.data;
    
    setToken(data.access_token);
    localStorage.setItem('ildo_token', data.access_token);

    const userProfile = {
      id: data.user_id,
      email: data.email,
      full_name: data.full_name,
      role: data.role,
    };
    setUser(userProfile);
    localStorage.setItem('ildo_user', JSON.stringify(userProfile));

    return data;
  };

  const register = async (formData) => {
    const response = await apiClient.post('/api/v1/auth/register', formData);
    return response.data;
  };

  const logout = () => {
    localStorage.removeItem('ildo_token');
    localStorage.removeItem('ildo_user');
    setToken(null);
    setUser(null);
  };

  const hasRole = (allowedRoles) => {
    if (!user) return false;
    return allowedRoles.includes(user.role);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        loading,
        isAuthenticated: Boolean(token && user),
        login,
        register,
        logout,
        hasRole,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
