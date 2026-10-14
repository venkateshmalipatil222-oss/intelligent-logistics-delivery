import React, { useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import Navbar from './components/Navbar';
import Footer from './components/Footer';
import HealthDashboard from './pages/HealthDashboard';
import Login from './pages/Login';
import Register from './pages/Register';
import Unauthorized from './pages/Unauthorized';
import ProtectedRoute from './components/ProtectedRoute';

import AdminPortal from './pages/admin/AdminPortal';
import WarehousePortal from './pages/warehouse/WarehousePortal';
import DriverPortal from './pages/driver/DriverPortal';
import CustomerPortal from './pages/customer/CustomerPortal';

function App() {
  const [health, setHealth] = useState(null);

  return (
    <AuthProvider>
      <BrowserRouter>
        <div className="flex flex-col min-h-screen bg-slate-950 text-slate-100 font-sans selection:bg-indigo-600 selection:text-white">
          <Navbar health={health} />
          
          <main className="flex-1">
            <Routes>
              {/* Public Routes */}
              <Route path="/" element={<HealthDashboard health={health} setHealth={setHealth} />} />
              <Route path="/health" element={<HealthDashboard health={health} setHealth={setHealth} />} />
              <Route path="/login" element={<Login />} />
              <Route path="/register" element={<Register />} />
              <Route path="/unauthorized" element={<Unauthorized />} />

              {/* Role-Protected Portals */}
              <Route
                path="/admin/*"
                element={
                  <ProtectedRoute allowedRoles={['ADMIN']}>
                    <AdminPortal />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/warehouse/*"
                element={
                  <ProtectedRoute allowedRoles={['ADMIN', 'WAREHOUSE_MANAGER']}>
                    <WarehousePortal />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/driver/*"
                element={
                  <ProtectedRoute allowedRoles={['ADMIN', 'DRIVER']}>
                    <DriverPortal />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/customer/*"
                element={
                  <ProtectedRoute allowedRoles={['ADMIN', 'CUSTOMER']}>
                    <CustomerPortal />
                  </ProtectedRoute>
                }
              />

              {/* Fallback */}
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </main>

          <Footer />
        </div>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
