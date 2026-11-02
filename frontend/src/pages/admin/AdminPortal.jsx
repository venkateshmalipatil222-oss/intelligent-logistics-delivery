import React, { useState, useEffect } from 'react';
import {
  Shield,
  Users,
  Warehouse,
  Truck,
  Package,
  Activity,
  Radio,
  MapPin,
  RefreshCw,
  Clock,
  CheckCircle2,
  AlertCircle,
  TrendingUp,
  Award,
  Zap,
  BarChart3,
  Star,
  ChevronRight,
  PieChart,
  Leaf,
  Trees,
  Globe,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import {
  listWarehouses,
  listVehicles,
  listDrivers,
  listDeliveries,
  getAnalyticsOverview,
  getDriverLeaderboard,
  getWarehouseUtilization,
  getGreenFleetAnalytics,
} from '../../api/client';
import { LiveTrackingMap } from '../../components/LiveTrackingMap';
import { useLiveTracking } from '../../hooks/useLiveTracking';

export default function AdminPortal() {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState('analytics'); // 'analytics' | 'surveillance' | 'green_fleet'
  const [overview, setOverview] = useState(null);
  const [leaderboard, setLeaderboard] = useState([]);
  const [warehouses, setWarehouses] = useState([]);
  const [deliveries, setDeliveries] = useState([]);
  const [greenFleet, setGreenFleet] = useState(null);
  const [selectedDeliveryId, setSelectedDeliveryId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const { trackingData, connectionStatus, refresh: refreshTracking } = useLiveTracking(
    selectedDeliveryId
  );

  const fetchAdminData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [overviewRes, leaderRes, whRes, delRes, greenRes] = await Promise.allSettled([
        getAnalyticsOverview(),
        getDriverLeaderboard({ limit: 10 }),
        getWarehouseUtilization(),
        listDeliveries(),
        getGreenFleetAnalytics(),
      ]);

      if (overviewRes.status === 'fulfilled') setOverview(overviewRes.value);
      if (leaderRes.status === 'fulfilled') setLeaderboard(leaderRes.value?.drivers || []);
      if (whRes.status === 'fulfilled') setWarehouses(whRes.value?.warehouses || []);
      if (greenRes.status === 'fulfilled') setGreenFleet(greenRes.value);

      const delList = delRes.status === 'fulfilled' ? delRes.value || [] : [];
      setDeliveries(delList);
      if (delList.length > 0 && !selectedDeliveryId) {
        setSelectedDeliveryId(delList[0].id);
      }
    } catch (err) {
      setError(err.normalizedMessage || 'Error loading executive analytics data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAdminData();
  }, []);

  return (
    <div className="max-w-7xl mx-auto px-6 py-8 space-y-6">
      {/* Header Bar */}
      <div className="flex flex-wrap items-center justify-between gap-4 pb-6 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-purple-500/10 text-purple-400 border border-purple-500/30 uppercase tracking-wider">
              Executive Command & Analytics
            </span>
            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 uppercase tracking-wider">
              Platform Level 1
            </span>
          </div>
          <h1 className="text-2xl font-extrabold text-white mt-1">Global Logistics & Operations Telemetry</h1>
          <p className="text-xs text-slate-400">
            Administrator: <span className="text-slate-200 font-semibold">{user.full_name}</span> ({user.email})
          </p>
        </div>

        <button
          onClick={fetchAdminData}
          disabled={loading}
          className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold border border-slate-700 flex items-center gap-2 transition disabled:opacity-50 cursor-pointer"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh Operations Telemetry</span>
        </button>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-950/60 border border-rose-500/40 text-rose-200 text-xs flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
            <span>{error}</span>
          </div>
          <button onClick={() => setError(null)} className="text-rose-400 hover:text-white font-bold ml-4">
            ✕
          </button>
        </div>
      )}

      {/* View 3: Sustainable Green Fleet & ESG CO2 Analytics (Phase 12) */}
      {activeTab === 'green_fleet' && (
        <div className="space-y-6">
          {/* Top ESG & CO2 Metric Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
            <div className="bg-slate-900 border border-emerald-500/30 rounded-2xl p-5 shadow-xl space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="font-bold text-slate-400 uppercase tracking-wider">CO2 Prevented</span>
                <div className="p-2 rounded-xl bg-emerald-500/20 text-emerald-400">
                  <Leaf className="w-4 h-4" />
                </div>
              </div>
              <div className="text-2xl font-black text-white font-mono">
                {greenFleet?.co2_emissions_prevented_kg || '0.00'} <span className="text-sm font-semibold text-emerald-400">kg</span>
              </div>
              <p className="text-[11px] text-slate-400">Compared against 100% diesel ICE baseline</p>
            </div>

            <div className="bg-slate-900 border border-indigo-500/30 rounded-2xl p-5 shadow-xl space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="font-bold text-slate-400 uppercase tracking-wider">EV Fleet Ratio</span>
                <div className="p-2 rounded-xl bg-indigo-500/20 text-indigo-400">
                  <Zap className="w-4 h-4" />
                </div>
              </div>
              <div className="text-2xl font-black text-white font-mono">
                {greenFleet?.ev_percentage || 0}%
              </div>
              <p className="text-[11px] text-slate-400">
                <b>{greenFleet?.ev_vehicles || 0}</b> Electric Vans & Bikes of {greenFleet?.total_vehicles || 0} assets
              </p>
            </div>

            <div className="bg-slate-900 border border-blue-500/30 rounded-2xl p-5 shadow-xl space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="font-bold text-slate-400 uppercase tracking-wider">Fuel Saved</span>
                <div className="p-2 rounded-xl bg-blue-500/20 text-blue-400">
                  <TrendingUp className="w-4 h-4" />
                </div>
              </div>
              <div className="text-2xl font-black text-white font-mono">
                {greenFleet?.fuel_liters_saved || 0} <span className="text-sm font-semibold text-blue-400">Liters</span>
              </div>
              <p className="text-[11px] text-slate-400">
                ₹{greenFleet?.fuel_cost_saved_inr?.toFixed(2) || '0.00'} saved in fossil fuel expenses
              </p>
            </div>

            <div className="bg-slate-900 border border-amber-500/30 rounded-2xl p-5 shadow-xl space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="font-bold text-slate-400 uppercase tracking-wider">ESG Rating</span>
                <div className="p-2 rounded-xl bg-amber-500/20 text-amber-400">
                  <Award className="w-4 h-4" />
                </div>
              </div>
              <div className="text-xl font-black text-white truncate">
                {greenFleet?.esg_rating || 'A+ Exemplary'}
              </div>
              <p className="text-[11px] text-slate-400 flex items-center gap-1">
                <Trees className="w-3.5 h-3.5 text-emerald-400" />
                <span>Equivalent to <b>{greenFleet?.trees_equivalent_planted || 0}</b> urban trees planted</span>
              </p>
            </div>
          </div>

          {/* Powertrain Fleet Comparison & Environmental Audit Table */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 pb-4">
              <div className="flex items-center space-x-3">
                <div className="w-9 h-9 rounded-xl bg-emerald-500/20 text-emerald-400 flex items-center justify-center border border-emerald-500/30">
                  <Globe className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-white">Powertrain Emission Benchmarks & Fleet Breakdown</h3>
                  <p className="text-xs text-slate-400">
                    Live telemetry calculated over {greenFleet?.total_distance_km || 0} km of dispatched routing
                  </p>
                </div>
              </div>
              <span className="px-3 py-1 rounded-full text-xs font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                Phase 12 ESG Certified
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-slate-800 text-slate-400 uppercase text-[10px] tracking-wider">
                    <th className="pb-3 px-3">Powertrain Type</th>
                    <th className="pb-3 px-3">Active Assets</th>
                    <th className="pb-3 px-3 text-center">CO2 Emission Factor</th>
                    <th className="pb-3 px-3 text-center">Fleet Share</th>
                    <th className="pb-3 px-3 text-right">Environmental Impact</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  <tr className="hover:bg-slate-950/40 transition">
                    <td className="py-3 px-3 flex items-center gap-2 font-bold text-white">
                      <Zap className="w-4 h-4 text-emerald-400" />
                      <span>Electric Vehicles (EV)</span>
                    </td>
                    <td className="py-3 px-3 font-mono text-emerald-300 font-bold">
                      {greenFleet?.ev_vehicles || 0} units
                    </td>
                    <td className="py-3 px-3 text-center font-mono text-emerald-400">0.0 g CO2 / km</td>
                    <td className="py-3 px-3 text-center font-bold text-white">
                      {greenFleet?.ev_percentage || 0}%
                    </td>
                    <td className="py-3 px-3 text-right">
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/20 text-emerald-300 uppercase">
                        Zero Tailpipe Emissions
                      </span>
                    </td>
                  </tr>

                  <tr className="hover:bg-slate-950/40 transition">
                    <td className="py-3 px-3 flex items-center gap-2 font-bold text-slate-300">
                      <Truck className="w-4 h-4 text-blue-400" />
                      <span>Diesel Cargo Vans</span>
                    </td>
                    <td className="py-3 px-3 font-mono text-slate-300">
                      {greenFleet?.diesel_vehicles || 0} units
                    </td>
                    <td className="py-3 px-3 text-center font-mono text-slate-400">185.0 g CO2 / km</td>
                    <td className="py-3 px-3 text-center font-bold text-slate-300">
                      {greenFleet?.total_vehicles ? Math.round(((greenFleet.diesel_vehicles || 0) / greenFleet.total_vehicles) * 100) : 0}%
                    </td>
                    <td className="py-3 px-3 text-right">
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/20 text-amber-300 uppercase">
                        Standard Freight
                      </span>
                    </td>
                  </tr>

                  <tr className="hover:bg-slate-950/40 transition">
                    <td className="py-3 px-3 flex items-center gap-2 font-bold text-slate-300">
                      <Activity className="w-4 h-4 text-amber-400" />
                      <span>Petrol Motorbikes</span>
                    </td>
                    <td className="py-3 px-3 font-mono text-slate-300">
                      {greenFleet?.petrol_vehicles || 0} units
                    </td>
                    <td className="py-3 px-3 text-center font-mono text-slate-400">68.0 g CO2 / km</td>
                    <td className="py-3 px-3 text-center font-bold text-slate-300">
                      {greenFleet?.total_vehicles ? Math.round(((greenFleet.petrol_vehicles || 0) / greenFleet.total_vehicles) * 100) : 0}%
                    </td>
                    <td className="py-3 px-3 text-right">
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-800 text-slate-300 uppercase">
                        Urban Courier
                      </span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Top Level KPI Telemetry Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Orders & Revenue */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-lg space-y-2">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-semibold uppercase tracking-wider">Gross Orders</span>
            <Package className="w-4 h-4 text-purple-400" />
          </div>
          <div className="text-3xl font-black text-white">
            {overview?.total_orders ?? '0'}
          </div>
          <div className="flex items-center justify-between text-[11px] pt-1 border-t border-slate-800">
            <span className="text-slate-400">Total Revenue:</span>
            <span className="text-emerald-400 font-mono font-bold">
              ₹{overview?.total_revenue_inr?.toFixed(2) ?? '0.00'}
            </span>
          </div>
        </div>

        {/* SLA On-Time Adherence */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-lg space-y-2">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-semibold uppercase tracking-wider">SLA Adherence Rate</span>
            <TrendingUp className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-black text-emerald-400">
              {overview?.sla_on_time_rate_pct ?? '100'}%
            </span>
            <span className="text-[10px] font-bold text-emerald-300 bg-emerald-500/20 px-1.5 py-0.5 rounded">
              Target: 95%
            </span>
          </div>
          <div className="flex items-center justify-between text-[11px] pt-1 border-t border-slate-800">
            <span className="text-slate-400">Avg Trip Duration:</span>
            <span className="text-slate-200 font-semibold font-mono">
              {overview?.average_delivery_duration_minutes ?? '0.0'} mins
            </span>
          </div>
        </div>

        {/* Active Dispatches vs Completed */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-lg space-y-2">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-semibold uppercase tracking-wider">Active Deliveries</span>
            <Activity className="w-4 h-4 text-blue-400" />
          </div>
          <div className="text-3xl font-black text-white">
            {overview?.active_deliveries ?? '0'}
          </div>
          <div className="flex items-center justify-between text-[11px] pt-1 border-t border-slate-800">
            <span className="text-slate-400">Completed:</span>
            <span className="text-slate-200 font-semibold">
              {overview?.completed_deliveries ?? '0'} delivered ({overview?.failed_deliveries ?? '0'} failed)
            </span>
          </div>
        </div>

        {/* Fleet Assets & EV Share */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-lg space-y-2">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-semibold uppercase tracking-wider">Fleet & EV Ratio</span>
            <Truck className="w-4 h-4 text-amber-400" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-black text-white">
              {overview?.fleet_summary?.total_vehicles ?? '0'}
            </span>
            <span className="text-[10px] font-bold text-emerald-400 bg-emerald-500/10 border border-emerald-500/30 px-2 py-0.5 rounded-full flex items-center gap-1">
              <Zap className="w-3 h-3" />
              {overview?.fleet_summary?.electric_percentage ?? '0'}% EV
            </span>
          </div>
          <div className="flex items-center justify-between text-[11px] pt-1 border-t border-slate-800">
            <span className="text-slate-400">Active In-Service:</span>
            <span className="text-slate-200 font-semibold">
              {overview?.fleet_summary?.active_vehicles ?? '0'} vehicles ({overview?.fleet_summary?.available_vehicles ?? '0'} available)
            </span>
          </div>
        </div>
      </div>

      {/* Navigation View Switcher */}
      <div className="flex items-center gap-2 border-b border-slate-800 pb-2">
        <button
          onClick={() => setActiveTab('analytics')}
          className={`px-4 py-2 rounded-xl text-xs font-bold transition flex items-center gap-2 cursor-pointer ${
            activeTab === 'analytics'
              ? 'bg-purple-600 text-white shadow-lg shadow-purple-500/20'
              : 'bg-slate-900 text-slate-400 hover:text-white hover:bg-slate-800 border border-slate-800'
          }`}
        >
          <BarChart3 className="w-3.5 h-3.5" />
          <span>Operational Analytics & Performance</span>
        </button>

        <button
          onClick={() => setActiveTab('surveillance')}
          className={`px-4 py-2 rounded-xl text-xs font-bold transition flex items-center gap-2 cursor-pointer ${
            activeTab === 'surveillance'
              ? 'bg-purple-600 text-white shadow-lg shadow-purple-500/20'
              : 'bg-slate-900 text-slate-400 hover:text-white hover:bg-slate-800 border border-slate-800'
          }`}
        >
          <Radio className="w-3.5 h-3.5" />
          <span>Live Fleet Surveillance Map ({deliveries.length})</span>
        </button>

        <button
          onClick={() => setActiveTab('green_fleet')}
          className={`px-4 py-2 rounded-xl text-xs font-bold transition flex items-center gap-2 cursor-pointer ${
            activeTab === 'green_fleet'
              ? 'bg-emerald-600 text-white shadow-lg shadow-emerald-500/20'
              : 'bg-slate-900 text-slate-400 hover:text-white hover:bg-slate-800 border border-slate-800'
          }`}
        >
          <Leaf className="w-3.5 h-3.5 text-emerald-400" />
          <span>Sustainable Green Fleet & ESG CO2 (Phase 12)</span>
        </button>
      </div>

      {/* View 1: Analytics & Operational Performance */}
      {activeTab === 'analytics' && (
        <div className="space-y-6">
          {/* Charts & Status Distributions Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Order Lifecycle Distribution Card */}
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-2">
                  <Package className="w-4 h-4 text-purple-400" />
                  <span>Order Lifecycle Funnel</span>
                </h3>
                <span className="text-[10px] text-slate-500 font-mono">By Status</span>
              </div>

              <div className="space-y-2.5">
                {[
                  { key: 'CREATED', label: 'Created', color: 'bg-slate-600' },
                  { key: 'CONFIRMED', label: 'Confirmed', color: 'bg-indigo-500' },
                  { key: 'PROCESSING', label: 'Processing in Hub', color: 'bg-amber-500' },
                  { key: 'READY_FOR_DISPATCH', label: 'Ready for Dispatch', color: 'bg-purple-500' },
                  { key: 'DISPATCHED', label: 'Dispatched', color: 'bg-blue-500' },
                  { key: 'DELIVERED', label: 'Delivered', color: 'bg-emerald-500' },
                  { key: 'FAILED', label: 'Failed', color: 'bg-rose-500' },
                ].map((item) => {
                  const count = overview?.order_status_distribution?.[item.key] || 0;
                  const total = overview?.total_orders || 1;
                  const pct = Math.round((count / total) * 100);

                  return (
                    <div key={item.key} className="space-y-1">
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-slate-300">{item.label}</span>
                        <span className="font-mono text-slate-400">
                          <b className="text-white">{count}</b> ({pct}%)
                        </span>
                      </div>
                      <div className="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden">
                        <div
                          className={`h-full ${item.color} rounded-full transition-all duration-500`}
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Delivery Priority Distribution Card */}
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-2">
                  <Zap className="w-4 h-4 text-amber-400" />
                  <span>Delivery Priority Matrix</span>
                </h3>
                <span className="text-[10px] text-slate-500 font-mono">SLA Tier</span>
              </div>

              <div className="space-y-3">
                {[
                  { key: 'URGENT', label: 'Urgent Express', badge: 'bg-rose-500/20 text-rose-300 border-rose-500/30' },
                  { key: 'HIGH', label: 'High Priority', badge: 'bg-amber-500/20 text-amber-300 border-amber-500/30' },
                  { key: 'MEDIUM', label: 'Medium (Standard)', badge: 'bg-blue-500/20 text-blue-300 border-blue-500/30' },
                  { key: 'LOW', label: 'Low (Economy)', badge: 'bg-slate-800 text-slate-400 border-slate-700' },
                ].map((tier) => {
                  const count = overview?.priority_distribution?.[tier.key] || 0;
                  return (
                    <div
                      key={tier.key}
                      className="p-3 bg-slate-950/70 border border-slate-800 rounded-xl flex items-center justify-between text-xs"
                    >
                      <div className="flex items-center gap-2">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${tier.badge}`}>
                          {tier.key}
                        </span>
                        <span className="text-slate-300 font-semibold">{tier.label}</span>
                      </div>
                      <span className="font-mono font-bold text-white text-sm">{count}</span>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Fleet Composition & Powertrain Card */}
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-2">
                  <Truck className="w-4 h-4 text-emerald-400" />
                  <span>Fleet Powertrain & Assets</span>
                </h3>
                <span className="text-[10px] text-emerald-400 font-semibold">Green Fleet</span>
              </div>

              <div className="space-y-3 text-xs">
                <div className="p-3 bg-emerald-950/30 border border-emerald-500/30 rounded-xl flex items-center justify-between">
                  <div className="flex items-center gap-2 text-emerald-300 font-semibold">
                    <Zap className="w-4 h-4 text-emerald-400" />
                    <span>Electric Vehicles (EV)</span>
                  </div>
                  <span className="font-mono font-bold text-white text-base">
                    {overview?.fleet_summary?.ev_count || 0}
                  </span>
                </div>

                <div className="p-3 bg-slate-950/70 border border-slate-800 rounded-xl flex items-center justify-between text-slate-300">
                  <div className="flex items-center gap-2 font-semibold">
                    <span>Diesel Fleet Vehicles</span>
                  </div>
                  <span className="font-mono font-bold text-white">
                    {overview?.fleet_summary?.diesel_count || 0}
                  </span>
                </div>

                <div className="p-3 bg-slate-950/70 border border-slate-800 rounded-xl flex items-center justify-between text-slate-300">
                  <div className="flex items-center gap-2 font-semibold">
                    <span>Petrol Express Bikes</span>
                  </div>
                  <span className="font-mono font-bold text-white">
                    {overview?.fleet_summary?.petrol_count || 0}
                  </span>
                </div>

                <div className="pt-2 border-t border-slate-800 text-[11px] text-slate-400 flex items-center justify-between">
                  <span>Drivers Pool:</span>
                  <span className="text-slate-200">
                    <b>{overview?.driver_summary?.available_drivers || 0}</b> available &bull;{' '}
                    <b>{overview?.driver_summary?.busy_drivers || 0}</b> busy
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Driver Performance Leaderboard Table */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 pb-4">
              <div className="flex items-center space-x-3">
                <div className="w-9 h-9 rounded-xl bg-amber-500/20 text-amber-400 flex items-center justify-center border border-amber-500/30">
                  <Award className="w-5 h-5" />
                </div>
                <div>
                  <h2 className="text-base font-bold text-white">Driver Performance Leaderboard</h2>
                  <p className="text-xs text-slate-400">
                    Ranked by completed dispatches, customer ratings, and delivery success rate.
                  </p>
                </div>
              </div>
              <span className="text-xs text-slate-400 font-mono">
                Top {leaderboard.length} Drivers
              </span>
            </div>

            {leaderboard.length === 0 ? (
              <div className="py-12 text-center text-slate-500 text-xs">
                No active driver records available for leaderboard ranking.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="border-b border-slate-800 text-slate-400 uppercase text-[10px] tracking-wider">
                      <th className="pb-3 px-3">Rank</th>
                      <th className="pb-3 px-3">Driver</th>
                      <th className="pb-3 px-3">License</th>
                      <th className="pb-3 px-3">Vehicle</th>
                      <th className="pb-3 px-3 text-center">Rating</th>
                      <th className="pb-3 px-3 text-center">Completed</th>
                      <th className="pb-3 px-3 text-center">Success Rate</th>
                      <th className="pb-3 px-3 text-right">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {leaderboard.map((drv) => (
                      <tr key={drv.driver_id} className="hover:bg-slate-950/40 transition">
                        <td className="py-3 px-3">
                          <span
                            className={`w-6 h-6 rounded-full inline-flex items-center justify-center font-bold text-xs ${
                              drv.rank === 1
                                ? 'bg-amber-500 text-slate-950 shadow-md shadow-amber-500/20'
                                : drv.rank === 2
                                ? 'bg-slate-300 text-slate-950'
                                : drv.rank === 3
                                ? 'bg-amber-700 text-white'
                                : 'bg-slate-800 text-slate-400'
                            }`}
                          >
                            {drv.rank}
                          </span>
                        </td>
                        <td className="py-3 px-3">
                          <div className="font-bold text-white">{drv.driver_name}</div>
                          {drv.phone && <div className="text-[11px] text-slate-500">{drv.phone}</div>}
                        </td>
                        <td className="py-3 px-3 font-mono text-slate-400">{drv.license_number}</td>
                        <td className="py-3 px-3 font-mono text-slate-300">
                          {drv.assigned_vehicle_registration || 'Unassigned'}
                        </td>
                        <td className="py-3 px-3 text-center">
                          <div className="inline-flex items-center gap-1 text-amber-400 font-bold">
                            <Star className="w-3.5 h-3.5 fill-amber-400" />
                            <span>{drv.rating.toFixed(1)}</span>
                          </div>
                        </td>
                        <td className="py-3 px-3 text-center font-bold text-white font-mono">
                          {drv.total_deliveries_completed}
                        </td>
                        <td className="py-3 px-3 text-center">
                          <span className="font-bold text-emerald-400 font-mono">
                            {drv.on_time_rate_pct}%
                          </span>
                        </td>
                        <td className="py-3 px-3 text-right">
                          <span
                            className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                              drv.status === 'AVAILABLE'
                                ? 'bg-emerald-500/20 text-emerald-300'
                                : drv.status === 'BUSY'
                                ? 'bg-amber-500/20 text-amber-300'
                                : 'bg-slate-800 text-slate-400'
                            }`}
                          >
                            {drv.status}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}

      {/* View 2: Live Fleet Surveillance Map */}
      {activeTab === 'surveillance' && (
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-5">
          <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 pb-4">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 rounded-xl bg-purple-500/20 text-purple-400 flex items-center justify-center">
                <Radio className="w-5 h-5 animate-pulse" />
              </div>
              <div>
                <h2 className="text-lg font-bold text-white">Live Delivery Surveillance & Telemetry</h2>
                <p className="text-xs text-slate-400">
                  Observe live driver location, trajectory polyline, and dynamic ETA calculation
                </p>
              </div>
            </div>

            {/* Delivery Selector Dropdown */}
            <div className="flex items-center space-x-3">
              <span className="text-xs text-slate-400 font-semibold uppercase">Surveillance Target:</span>
              <select
                value={selectedDeliveryId || ''}
                onChange={(e) => setSelectedDeliveryId(Number(e.target.value))}
                className="bg-slate-950 border border-slate-700 rounded-xl px-4 py-2 text-xs font-semibold text-white focus:outline-none focus:border-purple-500"
              >
                {deliveries.map((del) => (
                  <option key={del.id} value={del.id}>
                    {del.delivery_number} &bull; {del.status} (Order #{del.order_id})
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Live Tracking Map Component */}
          {selectedDeliveryId ? (
            <LiveTrackingMap
              trackingData={trackingData}
              connectionStatus={connectionStatus}
              onRefresh={refreshTracking}
            />
          ) : (
            <div className="py-12 text-center text-slate-500 text-xs">
              No active deliveries to display on the surveillance map.
            </div>
          )}
        </div>
      )}

      {/* View 3: Sustainable Green Fleet & ESG CO2 Analytics (Phase 12) */}
      {activeTab === 'green_fleet' && (
        <div className="space-y-6">
          {/* Top ESG & CO2 Metric Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
            <div className="bg-slate-900 border border-emerald-500/30 rounded-2xl p-5 shadow-xl space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="font-bold text-slate-400 uppercase tracking-wider">CO2 Prevented</span>
                <div className="p-2 rounded-xl bg-emerald-500/20 text-emerald-400">
                  <Leaf className="w-4 h-4" />
                </div>
              </div>
              <div className="text-2xl font-black text-white font-mono">
                {greenFleet?.co2_emissions_prevented_kg || '0.00'} <span className="text-sm font-semibold text-emerald-400">kg</span>
              </div>
              <p className="text-[11px] text-slate-400">Compared against 100% diesel ICE baseline</p>
            </div>

            <div className="bg-slate-900 border border-indigo-500/30 rounded-2xl p-5 shadow-xl space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="font-bold text-slate-400 uppercase tracking-wider">EV Fleet Ratio</span>
                <div className="p-2 rounded-xl bg-indigo-500/20 text-indigo-400">
                  <Zap className="w-4 h-4" />
                </div>
              </div>
              <div className="text-2xl font-black text-white font-mono">
                {greenFleet?.ev_percentage || 0}%
              </div>
              <p className="text-[11px] text-slate-400">
                <b>{greenFleet?.ev_vehicles || 0}</b> Electric Vans & Bikes of {greenFleet?.total_vehicles || 0} assets
              </p>
            </div>

            <div className="bg-slate-900 border border-blue-500/30 rounded-2xl p-5 shadow-xl space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="font-bold text-slate-400 uppercase tracking-wider">Fuel Saved</span>
                <div className="p-2 rounded-xl bg-blue-500/20 text-blue-400">
                  <TrendingUp className="w-4 h-4" />
                </div>
              </div>
              <div className="text-2xl font-black text-white font-mono">
                {greenFleet?.fuel_liters_saved || 0} <span className="text-sm font-semibold text-blue-400">Liters</span>
              </div>
              <p className="text-[11px] text-slate-400">
                ₹{greenFleet?.fuel_cost_saved_inr?.toFixed(2) || '0.00'} saved in fossil fuel expenses
              </p>
            </div>

            <div className="bg-slate-900 border border-amber-500/30 rounded-2xl p-5 shadow-xl space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="font-bold text-slate-400 uppercase tracking-wider">ESG Rating</span>
                <div className="p-2 rounded-xl bg-amber-500/20 text-amber-400">
                  <Award className="w-4 h-4" />
                </div>
              </div>
              <div className="text-xl font-black text-white truncate">
                {greenFleet?.esg_rating || 'A+ Exemplary'}
              </div>
              <p className="text-[11px] text-slate-400 flex items-center gap-1">
                <Trees className="w-3.5 h-3.5 text-emerald-400" />
                <span>Equivalent to <b>{greenFleet?.trees_equivalent_planted || 0}</b> urban trees planted</span>
              </p>
            </div>
          </div>

          {/* Powertrain Fleet Comparison & Environmental Audit Table */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 pb-4">
              <div className="flex items-center space-x-3">
                <div className="w-9 h-9 rounded-xl bg-emerald-500/20 text-emerald-400 flex items-center justify-center border border-emerald-500/30">
                  <Globe className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-white">Powertrain Emission Benchmarks & Fleet Breakdown</h3>
                  <p className="text-xs text-slate-400">
                    Live telemetry calculated over {greenFleet?.total_distance_km || 0} km of dispatched routing
                  </p>
                </div>
              </div>
              <span className="px-3 py-1 rounded-full text-xs font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                Phase 12 ESG Certified
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-slate-800 text-slate-400 uppercase text-[10px] tracking-wider">
                    <th className="pb-3 px-3">Powertrain Type</th>
                    <th className="pb-3 px-3">Active Assets</th>
                    <th className="pb-3 px-3 text-center">CO2 Emission Factor</th>
                    <th className="pb-3 px-3 text-center">Fleet Share</th>
                    <th className="pb-3 px-3 text-right">Environmental Impact</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  <tr className="hover:bg-slate-950/40 transition">
                    <td className="py-3 px-3 flex items-center gap-2 font-bold text-white">
                      <Zap className="w-4 h-4 text-emerald-400" />
                      <span>Electric Vehicles (EV)</span>
                    </td>
                    <td className="py-3 px-3 font-mono text-emerald-300 font-bold">
                      {greenFleet?.ev_vehicles || 0} units
                    </td>
                    <td className="py-3 px-3 text-center font-mono text-emerald-400">0.0 g CO2 / km</td>
                    <td className="py-3 px-3 text-center font-bold text-white">
                      {greenFleet?.ev_percentage || 0}%
                    </td>
                    <td className="py-3 px-3 text-right">
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/20 text-emerald-300 uppercase">
                        Zero Tailpipe Emissions
                      </span>
                    </td>
                  </tr>

                  <tr className="hover:bg-slate-950/40 transition">
                    <td className="py-3 px-3 flex items-center gap-2 font-bold text-slate-300">
                      <Truck className="w-4 h-4 text-blue-400" />
                      <span>Diesel Cargo Vans</span>
                    </td>
                    <td className="py-3 px-3 font-mono text-slate-300">
                      {greenFleet?.diesel_vehicles || 0} units
                    </td>
                    <td className="py-3 px-3 text-center font-mono text-slate-400">185.0 g CO2 / km</td>
                    <td className="py-3 px-3 text-center font-bold text-slate-300">
                      {greenFleet?.total_vehicles ? Math.round(((greenFleet.diesel_vehicles || 0) / greenFleet.total_vehicles) * 100) : 0}%
                    </td>
                    <td className="py-3 px-3 text-right">
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/20 text-amber-300 uppercase">
                        Standard Freight
                      </span>
                    </td>
                  </tr>

                  <tr className="hover:bg-slate-950/40 transition">
                    <td className="py-3 px-3 flex items-center gap-2 font-bold text-slate-300">
                      <Activity className="w-4 h-4 text-amber-400" />
                      <span>Petrol Motorbikes</span>
                    </td>
                    <td className="py-3 px-3 font-mono text-slate-300">
                      {greenFleet?.petrol_vehicles || 0} units
                    </td>
                    <td className="py-3 px-3 text-center font-mono text-slate-400">68.0 g CO2 / km</td>
                    <td className="py-3 px-3 text-center font-bold text-slate-300">
                      {greenFleet?.total_vehicles ? Math.round(((greenFleet.petrol_vehicles || 0) / greenFleet.total_vehicles) * 100) : 0}%
                    </td>
                    <td className="py-3 px-3 text-right">
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-800 text-slate-300 uppercase">
                        Urban Courier
                      </span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
