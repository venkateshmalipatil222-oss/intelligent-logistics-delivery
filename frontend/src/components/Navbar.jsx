import React from 'react';
import { Truck, ShieldCheck, Activity, Layers, Server } from 'lucide-react';

export default function Navbar({ health }) {
  const isHealthy = health?.status === 'healthy';

  return (
    <header className="sticky top-0 z-50 bg-slate-900/90 backdrop-blur-md border-b border-slate-800 px-6 py-3.5 shadow-lg">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        {/* Brand */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-blue-600 flex items-center justify-center shadow-md shadow-indigo-500/20">
            <Truck className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-extrabold text-lg tracking-tight bg-gradient-to-r from-white via-slate-200 to-indigo-300 bg-clip-text text-transparent">
                ILDO Platform
              </span>
              <span className="text-[10px] font-semibold tracking-wider uppercase px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                v1.0-alpha
              </span>
            </div>
            <p className="text-xs text-slate-400 font-medium">Intelligent Logistics & Delivery Optimization</p>
          </div>
        </div>

        {/* System Telemetry & Status Badge */}
        <div className="flex items-center gap-4">
          <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800/80 border border-slate-700/60 text-xs text-slate-300">
            <Server className="w-3.5 h-3.5 text-slate-400" />
            <span>FastAPI REST & WS</span>
            <span className="text-slate-600">•</span>
            <span className="text-slate-400">MySQL 8</span>
          </div>

          <div
            className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-semibold border transition-all ${
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
            <span>{isHealthy ? 'System Operational' : 'Checking Backend...'}</span>
          </div>
        </div>
      </div>
    </header>
  );
}
