import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Truck, ShieldCheck, Activity, Server, LogOut, User, LogIn, UserPlus } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function Navbar({ health }) {
  const { user, isAuthenticated, logout } = useAuth();
  const navigate = useNavigate();
  const isHealthy = health?.status === 'healthy';

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const getRoleBadgeColor = (role) => {
    switch (role) {
      case 'ADMIN':
        return 'bg-purple-500/10 text-purple-400 border-purple-500/30';
      case 'WAREHOUSE_MANAGER':
        return 'bg-blue-500/10 text-blue-400 border-blue-500/30';
      case 'DRIVER':
        return 'bg-amber-500/10 text-amber-400 border-amber-500/30';
      case 'CUSTOMER':
        return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30';
      default:
        return 'bg-slate-500/10 text-slate-400 border-slate-500/30';
    }
  };

  return (
    <header className="sticky top-0 z-50 bg-slate-900/90 backdrop-blur-md border-b border-slate-800 px-6 py-3.5 shadow-lg">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        {/* Brand */}
        <Link to="/" className="flex items-center gap-3 group">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-blue-600 flex items-center justify-center shadow-md shadow-indigo-500/20 group-hover:scale-105 transition-all">
            <Truck className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-extrabold text-lg tracking-tight bg-gradient-to-r from-white via-slate-200 to-indigo-300 bg-clip-text text-transparent">
                ILDO Platform
              </span>
              <span className="text-[10px] font-semibold tracking-wider uppercase px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                v1.0
              </span>
            </div>
            <p className="text-xs text-slate-400 font-medium">Intelligent Logistics & Delivery Optimization</p>
          </div>
        </Link>

        {/* Center / Navigation Links */}
        <nav className="hidden md:flex items-center gap-1 text-xs font-semibold">
          <Link
            to="/health"
            className="px-3 py-1.5 rounded-lg text-slate-300 hover:text-white hover:bg-slate-800/80 transition-all flex items-center gap-1.5"
          >
            <Activity className="w-3.5 h-3.5 text-indigo-400" />
            <span>Health & Telemetry</span>
          </Link>

          {isAuthenticated && (
            <>
              {user.role === 'ADMIN' && (
                <Link
                  to="/admin"
                  className="px-3 py-1.5 rounded-lg text-slate-300 hover:text-white hover:bg-slate-800/80 transition-all"
                >
                  Admin Control
                </Link>
              )}
              {user.role === 'WAREHOUSE_MANAGER' && (
                <Link
                  to="/warehouse"
                  className="px-3 py-1.5 rounded-lg text-slate-300 hover:text-white hover:bg-slate-800/80 transition-all"
                >
                  Warehouse Hub
                </Link>
              )}
              {user.role === 'DRIVER' && (
                <Link
                  to="/driver"
                  className="px-3 py-1.5 rounded-lg text-slate-300 hover:text-white hover:bg-slate-800/80 transition-all"
                >
                  Driver Navigation
                </Link>
              )}
              {user.role === 'CUSTOMER' && (
                <Link
                  to="/customer"
                  className="px-3 py-1.5 rounded-lg text-slate-300 hover:text-white hover:bg-slate-800/80 transition-all"
                >
                  My Deliveries
                </Link>
              )}
            </>
          )}
        </nav>

        {/* Right Section: Status Badge & Auth Controls */}
        <div className="flex items-center gap-3">
          {/* Liveness Indicator */}
          <div
            className={`hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-semibold border transition-all ${
              isHealthy
                ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                : 'bg-amber-500/10 text-amber-400 border-amber-500/30'
            }`}
          >
            <span
              className={`w-2 h-2 rounded-full ${
                isHealthy ? 'bg-emerald-400 animate-pulse' : 'bg-amber-400'
              }`}
            />
            <span>{isHealthy ? 'Live MySQL 8' : 'Connecting...'}</span>
          </div>

          {/* User Controls */}
          {isAuthenticated ? (
            <div className="flex items-center gap-2.5">
              <div className="flex flex-col items-end">
                <span className="text-xs font-bold text-white leading-tight">{user.full_name}</span>
                <span className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.2 rounded-full border ${getRoleBadgeColor(user.role)}`}>
                  {user.role}
                </span>
              </div>

              <button
                onClick={handleLogout}
                title="Sign Out"
                className="p-2 rounded-lg bg-slate-800 hover:bg-red-950/40 text-slate-300 hover:text-red-300 border border-slate-700/80 hover:border-red-800/60 transition-all"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          ) : (
            <div className="flex items-center gap-2 text-xs">
              <Link
                to="/login"
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800/80 hover:bg-slate-800 text-slate-200 border border-slate-700/80 font-semibold transition-all"
              >
                <LogIn className="w-3.5 h-3.5 text-slate-400" />
                <span>Sign In</span>
              </Link>

              <Link
                to="/register"
                className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-semibold shadow-md shadow-indigo-600/30 transition-all"
              >
                <UserPlus className="w-3.5 h-3.5" />
                <span>Register</span>
              </Link>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
