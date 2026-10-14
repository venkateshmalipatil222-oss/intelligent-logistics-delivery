import React from 'react';
import { Shield, Users, Warehouse, Truck, Package, ArrowRight } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

export default function AdminPortal() {
  const { user } = useAuth();

  return (
    <div className="max-w-7xl mx-auto px-6 py-8 space-y-6">
      <div className="flex items-center justify-between pb-6 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-purple-500/10 text-purple-400 border border-purple-500/30 uppercase">
              Admin Access Granted
            </span>
          </div>
          <h1 className="text-2xl font-extrabold text-white mt-2">Executive Logistics & Fleet Command</h1>
          <p className="text-xs text-slate-400 mt-1">Logged in as {user.full_name} ({user.email})</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Access Scope</span>
            <Shield className="w-4 h-4 text-purple-400" />
          </div>
          <div className="text-lg font-bold text-white mb-1">Global System Authority</div>
          <p className="text-xs text-slate-400">Full administrative management over users, warehouses, fleet, route algorithms, and security audits.</p>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Authentication State</span>
            <Users className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-lg font-bold text-white mb-1">RBAC Active</div>
          <p className="text-xs text-slate-400">JWT Claims verified: role matches ADMIN. Direct access to `/api/v1/users` authorized.</p>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Next Modules</span>
            <Package className="w-4 h-4 text-indigo-400" />
          </div>
          <div className="text-lg font-bold text-white mb-1">Phase 3 Ready</div>
          <p className="text-xs text-slate-400">Warehouse hubs, package staging queues, and driver fleet tracking ready for Core Logistics pipeline.</p>
        </div>
      </div>
    </div>
  );
}
