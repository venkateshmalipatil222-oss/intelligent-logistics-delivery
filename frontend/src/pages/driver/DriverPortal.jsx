import React from 'react';
import { Navigation, MapPin, CheckCircle, Smartphone } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

export default function DriverPortal() {
  const { user } = useAuth();

  return (
    <div className="max-w-7xl mx-auto px-6 py-8 space-y-6">
      <div className="pb-6 border-b border-slate-800">
        <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-amber-500/10 text-amber-400 border border-amber-500/30 uppercase">
          Driver Mobile Console
        </span>
        <h1 className="text-2xl font-extrabold text-white mt-2">Active Route & Navigation Console</h1>
        <p className="text-xs text-slate-400 mt-1">Logged in as {user.full_name} ({user.email})</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">GPS Live Streaming</span>
            <Navigation className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-lg font-bold text-white mb-1">Browser Geolocation API</div>
          <p className="text-xs text-slate-400">Device location updates will stream directly to the backend WebSocket server upon driver permission.</p>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Proof of Delivery</span>
            <CheckCircle className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-lg font-bold text-white mb-1">OTP Verification Workflow</div>
          <p className="text-xs text-slate-400">Cryptographically secure OTP submission to complete deliveries at customer drop-offs.</p>
        </div>
      </div>
    </div>
  );
}
