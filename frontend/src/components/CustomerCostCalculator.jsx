import React, { useState, useEffect } from 'react';
import {
  Calculator,
  Truck,
  Zap,
  ShieldCheck,
  AlertCircle,
  HelpCircle,
  Clock,
  Sparkles,
  RefreshCw,
  Coins,
  ChevronDown,
} from 'lucide-react';
import { estimateCost } from '../api/client';

export default function CustomerCostCalculator({ onPreFillBooking }) {
  const [distanceKm, setDistanceKm] = useState(18.5);
  const [weightKg, setWeightKg] = useState(3.5);
  const [vehicleType, setVehicleType] = useState('VAN');
  const [priority, setPriority] = useState('MEDIUM');
  const [requiresColdStorage, setRequiresColdStorage] = useState(false);

  const [loading, setLoading] = useState(false);
  const [quote, setQuote] = useState(null);
  const [error, setError] = useState(null);

  const calculateQuote = async () => {
    if (distanceKm <= 0 || weightKg <= 0) return;
    setLoading(true);
    setError(null);
    try {
      const data = await estimateCost({
        distance_km: Number(distanceKm),
        package_weight_kg: Number(weightKg),
        package_volume_m3: 0.005,
        vehicle_type: vehicleType,
        priority: priority,
        requires_cold_storage: requiresColdStorage,
      });
      setQuote(data);
    } catch (err) {
      setError(err.normalizedMessage || 'Failed to estimate delivery costs');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    calculateQuote();
  }, [distanceKm, weightKg, vehicleType, priority, requiresColdStorage]);

  const distancePresets = [5, 15, 30, 60];
  const weightPresets = [1, 5, 15, 30];

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-emerald-500/20 text-emerald-400 flex items-center justify-center border border-emerald-500/30">
            <Calculator className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <span>Transparent Delivery Cost Estimator</span>
              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 uppercase">
                Zero Hidden Fees
              </span>
            </h2>
            <p className="text-xs text-slate-400">
              Calculate instant, transparent shipping costs itemized by fuel, labor, distance, and vehicle type.
            </p>
          </div>
        </div>

        <button
          onClick={calculateQuote}
          disabled={loading}
          className="px-3.5 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold border border-slate-700 flex items-center gap-2 transition disabled:opacity-50 cursor-pointer"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Recalculate</span>
        </button>
      </div>

      {error && (
        <div className="p-3.5 rounded-xl bg-rose-950/60 border border-rose-500/40 text-rose-200 text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Input Parameters & Live Results Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Form Inputs (Left 7 Cols) */}
        <div className="lg:col-span-7 space-y-4">
          {/* Distance Input */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between text-xs">
              <label className="font-semibold text-slate-300">Delivery Distance (km)</label>
              <span className="font-mono text-emerald-400 font-bold">{distanceKm} km</span>
            </div>
            <div className="flex items-center gap-2">
              <input
                type="number"
                min="0.5"
                max="500"
                step="0.5"
                value={distanceKm}
                onChange={(e) => setDistanceKm(Math.max(0.1, Number(e.target.value)))}
                className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3.5 py-2 text-xs font-semibold text-white focus:outline-none focus:border-emerald-500"
              />
              <div className="flex items-center gap-1">
                {distancePresets.map((d) => (
                  <button
                    key={d}
                    type="button"
                    onClick={() => setDistanceKm(d)}
                    className={`px-2.5 py-2 rounded-xl text-xs font-semibold border transition ${
                      distanceKm === d
                        ? 'bg-emerald-500/20 border-emerald-500/40 text-emerald-300'
                        : 'bg-slate-950 border-slate-800 hover:border-slate-700 text-slate-400'
                    }`}
                  >
                    {d}km
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Weight Input */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between text-xs">
              <label className="font-semibold text-slate-300">Package Weight (kg)</label>
              <span className="font-mono text-emerald-400 font-bold">{weightKg} kg</span>
            </div>
            <div className="flex items-center gap-2">
              <input
                type="number"
                min="0.1"
                max="200"
                step="0.1"
                value={weightKg}
                onChange={(e) => setWeightKg(Math.max(0.1, Number(e.target.value)))}
                className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3.5 py-2 text-xs font-semibold text-white focus:outline-none focus:border-emerald-500"
              />
              <div className="flex items-center gap-1">
                {weightPresets.map((w) => (
                  <button
                    key={w}
                    type="button"
                    onClick={() => setWeightKg(w)}
                    className={`px-2.5 py-2 rounded-xl text-xs font-semibold border transition ${
                      weightKg === w
                        ? 'bg-emerald-500/20 border-emerald-500/40 text-emerald-300'
                        : 'bg-slate-950 border-slate-800 hover:border-slate-700 text-slate-400'
                    }`}
                  >
                    {w}kg
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Vehicle Type & Priority */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-300">Vehicle Carrier</label>
              <select
                value={vehicleType}
                onChange={(e) => setVehicleType(e.target.value)}
                className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3.5 py-2 text-xs font-semibold text-white focus:outline-none focus:border-emerald-500"
              >
                <option value="BIKE">BIKE (Parcel &lt;15kg - Low Cost)</option>
                <option value="VAN">VAN (Standard Carrier - 1000kg)</option>
                <option value="ELECTRIC_VAN">ELECTRIC_VAN (Eco-Friendly EV)</option>
                <option value="TRUCK">TRUCK (Heavy Freight - 5000kg)</option>
              </select>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-300">Delivery Priority</label>
              <select
                value={priority}
                onChange={(e) => setPriority(e.target.value)}
                className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3.5 py-2 text-xs font-semibold text-white focus:outline-none focus:border-emerald-500"
              >
                <option value="LOW">LOW (Economy - Next Day)</option>
                <option value="MEDIUM">MEDIUM (Standard Same-Day)</option>
                <option value="HIGH">HIGH (Priority Routing)</option>
                <option value="URGENT">URGENT (Express ASAP)</option>
              </select>
            </div>
          </div>

          {/* Cold Storage Toggle */}
          <div className="pt-2">
            <label className="flex items-center gap-3 p-3 bg-slate-950/60 border border-slate-800 rounded-xl cursor-pointer hover:border-slate-700 transition">
              <input
                type="checkbox"
                checked={requiresColdStorage}
                onChange={(e) => setRequiresColdStorage(e.target.checked)}
                className="w-4 h-4 rounded text-emerald-500 focus:ring-emerald-500 border-slate-700 bg-slate-900"
              />
              <div className="text-xs">
                <span className="font-semibold text-white">Requires Cold Storage Refrigeration</span>
                <p className="text-[11px] text-slate-400">
                  Adds temperature-controlled refrigeration unit operating charge (+15%).
                </p>
              </div>
            </label>
          </div>
        </div>

        {/* Live Itemized Breakdown (Right 5 Cols) */}
        <div className="lg:col-span-5 bg-slate-950/80 border border-slate-800 rounded-2xl p-5 flex flex-col justify-between space-y-4">
          <div>
            <div className="flex items-center justify-between text-xs text-slate-400 border-b border-slate-800 pb-2">
              <span className="uppercase tracking-wider font-semibold">Cost Breakdown</span>
              <span className="text-emerald-400 font-mono">18% GST Applicable</span>
            </div>

            {quote ? (
              <div className="mt-4 space-y-2.5">
                <div className="flex items-center justify-between text-xs text-slate-300">
                  <span>Dispatch Base Fee</span>
                  <span className="font-mono text-slate-200">₹{quote.dispatch_base_fee_inr.toFixed(2)}</span>
                </div>
                <div className="flex items-center justify-between text-xs text-slate-300">
                  <span>Fuel / Energy Consumption</span>
                  <span className="font-mono text-slate-200">₹{quote.fuel_expense_inr.toFixed(2)}</span>
                </div>
                <div className="flex items-center justify-between text-xs text-slate-300">
                  <span>Driver Labor Hours</span>
                  <span className="font-mono text-slate-200">₹{quote.driver_labor_inr.toFixed(2)}</span>
                </div>
                <div className="flex items-center justify-between text-xs text-slate-300">
                  <span>Fleet Depreciation & Maintenance</span>
                  <span className="font-mono text-slate-200">₹{quote.vehicle_maintenance_inr.toFixed(2)}</span>
                </div>
                {quote.priority_surcharge_inr > 0 && (
                  <div className="flex items-center justify-between text-xs text-amber-300">
                    <span>Priority Surcharge ({priority})</span>
                    <span className="font-mono">+₹{quote.priority_surcharge_inr.toFixed(2)}</span>
                  </div>
                )}
                {quote.cold_storage_surcharge_inr > 0 && (
                  <div className="flex items-center justify-between text-xs text-blue-300">
                    <span>Cold Storage Refrigeration</span>
                    <span className="font-mono">+₹{quote.cold_storage_surcharge_inr.toFixed(2)}</span>
                  </div>
                )}

                <div className="pt-2 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400">
                  <span>Subtotal</span>
                  <span className="font-mono text-slate-300">₹{quote.subtotal_inr.toFixed(2)}</span>
                </div>
                <div className="flex items-center justify-between text-xs text-slate-400">
                  <span>Freight GST (18%)</span>
                  <span className="font-mono text-slate-300">₹{quote.tax_gst_inr.toFixed(2)}</span>
                </div>

                <div className="p-3 bg-gradient-to-r from-emerald-950/40 to-slate-900 border border-emerald-500/30 rounded-xl mt-3 flex items-center justify-between">
                  <div>
                    <div className="text-[10px] text-emerald-400 uppercase tracking-widest font-bold">
                      Total Guaranteed Quote
                    </div>
                    <div className="text-2xl font-black text-white font-mono mt-0.5">
                      ₹{quote.total_estimated_cost_inr.toFixed(2)}
                    </div>
                  </div>
                  <Coins className="w-8 h-8 text-emerald-400 opacity-80" />
                </div>

                <div className="text-[11px] text-slate-500 pt-1 leading-relaxed">
                  {quote.calculation_explanation}
                </div>
              </div>
            ) : (
              <div className="py-12 text-center text-slate-500 text-xs">
                Enter shipping parameters to compute instant quote.
              </div>
            )}
          </div>

          <div className="pt-2 border-t border-slate-800/80">
            <div className="flex items-center gap-1.5 text-[11px] text-slate-400">
              <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0" />
              <span>Quotes remain valid for 24 hours from calculation.</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
