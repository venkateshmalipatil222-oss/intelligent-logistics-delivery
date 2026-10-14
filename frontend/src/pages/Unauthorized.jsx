import React from 'react';
import { useLocation, Link, useNavigate } from 'react-router-dom';
import { ShieldAlert, ArrowLeft, Home, LogOut } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function Unauthorized() {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const requiredRoles = location.state?.required || [];

  return (
    <div className="max-w-2xl mx-auto px-6 py-20 text-center">
      <div className="w-16 h-16 rounded-2xl bg-red-500/10 border border-red-500/20 text-red-400 flex items-center justify-center mx-auto mb-6 shadow-lg shadow-red-500/10">
        <ShieldAlert className="w-8 h-8" />
      </div>

      <h1 className="text-3xl font-extrabold text-white tracking-tight mb-3">
        403 - Access Denied
      </h1>
      <p className="text-slate-400 text-sm max-w-md mx-auto mb-6">
        Your authenticated account does not possess the required role permissions to view or interact with this resource.
      </p>

      {/* Role Comparison Card */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 mb-8 max-w-md mx-auto text-left text-xs space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-slate-400">Your Current Role:</span>
          <span className="px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 font-bold uppercase">
            {user?.role || 'Guest'}
          </span>
        </div>
        {requiredRoles.length > 0 && (
          <div className="flex items-center justify-between pt-2 border-t border-slate-800">
            <span className="text-slate-400">Required Role(s):</span>
            <span className="text-amber-400 font-semibold font-mono">
              {requiredRoles.join(', ')}
            </span>
          </div>
        )}
      </div>

      <div className="flex flex-wrap items-center justify-center gap-3">
        <button
          onClick={() => navigate(-1)}
          className="flex items-center gap-2 px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold border border-slate-700 transition-all"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Go Back</span>
        </button>

        <Link
          to="/"
          className="flex items-center gap-2 px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-md shadow-indigo-600/30 transition-all"
        >
          <Home className="w-4 h-4" />
          <span>System Overview</span>
        </Link>

        <button
          onClick={logout}
          className="flex items-center gap-2 px-4 py-2 rounded-lg bg-red-950/40 hover:bg-red-900/60 text-red-300 text-xs font-semibold border border-red-800/60 transition-all"
        >
          <LogOut className="w-4 h-4" />
          <span>Sign Out</span>
        </button>
      </div>
    </div>
  );
}
