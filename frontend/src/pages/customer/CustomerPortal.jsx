import React from 'react';
import { Package, MapPin, Clock, ShieldCheck } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

export default function CustomerPortal() {
  const { user } = useAuth();

  return (
    <div className="max-w-7xl mx-auto px-6 py-8 space-y-6">
      <div className="pb-6 border-b border-slate-800">
        <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 uppercase">
          Customer Portal
        </span>
        <h1 className="text-2xl font-extrabold text-white mt-2">Shipment Tracking & Order Center</h1>
        <p className="text-xs text-slate-400 mt-1">Logged in as {user.full_name} ({user.email})</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Order Management</span>
            <Package className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-lg font-bold text-white mb-1">Create & Track Shipments</div>
          <p className="text-xs text-slate-400">Place orders, customize package priority, view transparent cost estimates, and track authorized deliveries.</p>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Live ETA & Map</span>
            <Clock className="w-4 h-4 text-indigo-400" />
          </div>
          <div className="text-lg font-bold text-white mb-1">Interactive OpenStreetMap</div>
          <p className="text-xs text-slate-400">Real-time driver location updates on Leaflet map with dynamic ETA and delay risk alerts.</p>
        </div>
      </div>
    </div>
  );
}
