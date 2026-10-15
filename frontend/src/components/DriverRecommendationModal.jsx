import React, { useState, useEffect } from 'react';
import {
  Sparkles,
  UserCheck,
  Truck,
  CheckCircle2,
  AlertCircle,
  X,
  Gauge,
  Navigation,
  Star,
  ShieldCheck,
  Send,
  RefreshCw,
} from 'lucide-react';
import { recommendDriverForOrder, autoAssignDriver } from '../api/client';

export default function DriverRecommendationModal({
  order,
  isOpen,
  onClose,
  onDispatchSuccess,
}) {
  const [loading, setLoading] = useState(false);
  const [assigning, setAssigning] = useState(false);
  const [recommendations, setRecommendations] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (isOpen && order?.id) {
      fetchRecommendations();
    } else {
      setRecommendations(null);
      setError(null);
    }
  }, [isOpen, order?.id]);

  const fetchRecommendations = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await recommendDriverForOrder(order.id);
      setRecommendations(data);
    } catch (err) {
      setError(err.normalizedMessage || 'Failed to generate AI recommendations');
    } finally {
      setLoading(false);
    }
  };

  const handleAutoAssign = async () => {
    if (!order?.id) return;
    setAssigning(true);
    setError(null);
    try {
      const result = await autoAssignDriver(order.id);
      if (onDispatchSuccess) {
        onDispatchSuccess(result);
      }
      onClose();
    } catch (err) {
      setError(err.normalizedMessage || 'Failed to auto-assign driver');
    } finally {
      setAssigning(false);
    }
  };

  if (!isOpen || !order) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="relative w-full max-w-2xl bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-slate-800 bg-slate-900/60">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-purple-500/20 text-purple-400 flex items-center justify-center border border-purple-500/30">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <span>AI Driver Assignment Recommendation</span>
                <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-purple-500/20 text-purple-300 uppercase">
                  Multi-Factor Engine
                </span>
              </h3>
              <p className="text-xs text-slate-400">
                Order <span className="font-mono text-slate-200">{order.order_number}</span> &bull;{' '}
                {order.destination_city} &bull; {order.package?.weight_kg || '1.0'} kg
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="p-6 overflow-y-auto space-y-5">
          {error && (
            <div className="p-3.5 rounded-xl bg-rose-950/60 border border-rose-500/40 text-rose-200 text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {loading ? (
            <div className="py-12 text-center text-slate-400 space-y-3">
              <RefreshCw className="w-8 h-8 mx-auto animate-spin text-purple-400" />
              <p className="text-xs">Computing multi-factor constraint satisfaction & driver scores...</p>
            </div>
          ) : recommendations ? (
            <>
              {/* Algorithm Summary Banner */}
              <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-semibold text-slate-300">Scoring Formula</span>
                  <span className="text-[11px] text-purple-400 font-mono">
                    Proximity (35%) + Workload (25%) + Rating (20%) + Suitability (20%)
                  </span>
                </div>
                <div className="text-[11px] text-slate-400 leading-relaxed">
                  Evaluated {recommendations.eligible_candidates_count} eligible drivers across available fleet.
                </div>
              </div>

              {/* Recommended Candidate Card */}
              {recommendations.recommended_driver_id && recommendations.candidates?.length > 0 ? (
                <div className="p-4 rounded-xl bg-gradient-to-br from-purple-950/40 via-slate-900 to-indigo-950/40 border border-purple-500/40 space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 flex items-center gap-1">
                        <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                        Top Recommendation (#1)
                      </span>
                    </div>
                    <div className="text-right">
                      <span className="text-2xl font-black text-purple-400">
                        {recommendations.candidates[0].total_score}%
                      </span>
                      <span className="text-[10px] text-slate-400 ml-1">match</span>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-1 text-xs">
                    <div className="p-2.5 bg-slate-950/60 rounded-lg border border-slate-800">
                      <div className="text-[10px] text-slate-400 uppercase font-semibold">Driver</div>
                      <div className="text-white font-bold truncate mt-0.5">
                        {recommendations.candidates[0].driver_name}
                      </div>
                      <div className="text-[10px] text-slate-400 font-mono truncate">
                        {recommendations.candidates[0].license_number}
                      </div>
                    </div>

                    <div className="p-2.5 bg-slate-950/60 rounded-lg border border-slate-800">
                      <div className="text-[10px] text-slate-400 uppercase font-semibold">Vehicle</div>
                      <div className="text-white font-bold truncate mt-0.5">
                        {recommendations.candidates[0].vehicle_type || 'VAN'}
                      </div>
                      <div className="text-[10px] text-slate-400 font-mono truncate">
                        {recommendations.candidates[0].vehicle_registration || 'Fleet'}
                      </div>
                    </div>

                    <div className="p-2.5 bg-slate-950/60 rounded-lg border border-slate-800">
                      <div className="text-[10px] text-slate-400 uppercase font-semibold">Proximity</div>
                      <div className="text-emerald-400 font-bold mt-0.5">
                        {recommendations.candidates[0].proximity_km.toFixed(1)} km away
                      </div>
                      <div className="text-[10px] text-slate-400">Hub Distance</div>
                    </div>

                    <div className="p-2.5 bg-slate-950/60 rounded-lg border border-slate-800">
                      <div className="text-[10px] text-slate-400 uppercase font-semibold">Rating & Load</div>
                      <div className="text-amber-400 font-bold flex items-center gap-1 mt-0.5">
                        <Star className="w-3 h-3 fill-amber-400" />
                        <span>{recommendations.candidates[0].rating.toFixed(1)}</span>
                      </div>
                      <div className="text-[10px] text-slate-400">
                        {recommendations.candidates[0].active_deliveries_count} active deliveries
                      </div>
                    </div>
                  </div>

                  {/* Recommendation Rationale */}
                  <div className="p-3 bg-purple-950/20 border border-purple-500/20 rounded-lg text-xs text-purple-200/90 leading-relaxed">
                    <span className="font-semibold text-purple-300">AI Rationale: </span>
                    {recommendations.candidates[0].recommendation_rationale}
                  </div>
                </div>
              ) : (
                <div className="p-6 text-center text-slate-400 bg-slate-950 rounded-xl border border-slate-800 text-xs">
                  No eligible drivers currently available matching payload capacity and status constraints.
                </div>
              )}

              {/* Other Ranked Candidates */}
              {recommendations.candidates?.length > 1 && (
                <div className="space-y-2">
                  <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider">
                    Alternative Evaluated Drivers ({recommendations.candidates.length - 1})
                  </h4>
                  <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
                    {recommendations.candidates.slice(1).map((cand, idx) => (
                      <div
                        key={cand.driver_id}
                        className="p-3 rounded-xl bg-slate-950/70 border border-slate-800 flex items-center justify-between text-xs"
                      >
                        <div className="space-y-0.5">
                          <div className="font-semibold text-white flex items-center gap-2">
                            <span>#{idx + 2} {cand.driver_name}</span>
                            <span className="text-[10px] text-slate-400 font-mono">({cand.license_number})</span>
                          </div>
                          <div className="text-[11px] text-slate-400">
                            {cand.proximity_km.toFixed(1)} km &bull; {cand.vehicle_type} &bull; Rating {cand.rating.toFixed(1)}
                          </div>
                        </div>

                        <div className="text-right">
                          <div className="font-bold text-slate-200">{cand.total_score}%</div>
                          <div className="text-[10px] text-slate-500">score</div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          ) : null}
        </div>

        {/* Modal Footer */}
        <div className="p-5 border-t border-slate-800 bg-slate-900/60 flex items-center justify-between gap-3">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold border border-slate-700 transition cursor-pointer"
          >
            Cancel
          </button>

          <button
            onClick={handleAutoAssign}
            disabled={
              assigning ||
              loading ||
              !recommendations?.recommended_driver_id ||
              recommendations?.candidates?.length === 0
            }
            className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white text-xs font-bold shadow-lg shadow-purple-500/20 transition flex items-center gap-2 disabled:opacity-50 cursor-pointer"
          >
            {assigning ? (
              <>
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                <span>Auto-Assigning & Dispatched...</span>
              </>
            ) : (
              <>
                <Send className="w-3.5 h-3.5" />
                <span>1-Click Auto-Assign & Dispatch</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
