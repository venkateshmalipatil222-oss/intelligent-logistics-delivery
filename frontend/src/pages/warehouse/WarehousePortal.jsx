import React from 'react';
import { Warehouse, PackageCheck, Truck } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

export default function WarehousePortal() {
  const { user } = useAuth();

  return (
    <div className="max-w-7xl mx-auto px-6 py-8 space-y-6">
      <div className="pb-6 border-b border-slate-800">
        <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-blue-500/10 text-blue-400 border border-blue-500/30 uppercase">
          Warehouse Operations
        </span>
        <h1 className="text-2xl font-extrabold text-white mt-2">Warehouse Dispatch & Staging Hub</h1>
        <p className="text-xs text-slate-400 mt-1">Logged in as {user.full_name} ({user.email})</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Operational Scope</span>
            <Warehouse className="w-4 h-4 text-blue-400" />
          </div>
          <div className="text-lg font-bold text-white mb-1">Package Preparation & Readiness</div>
          <p className="text-xs text-slate-400">Order verification, weight/dimension logging, readiness staging, and driver vehicle load inspections.</p>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Dispatch Authorization</span>
            <Truck className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-lg font-bold text-white mb-1">Fleet Integration</div>
          <p className="text-xs text-slate-400">View available vehicles and assigned drivers ready for warehouse pickup and multi-stop dispatch.</p>
        </div>
      </div>
    </div>
  );
}
