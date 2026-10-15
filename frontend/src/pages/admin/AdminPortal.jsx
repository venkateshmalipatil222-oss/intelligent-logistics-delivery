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
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import {
  listWarehouses,
  listVehicles,
  listDrivers,
  listDeliveries,
} from '../../api/client';
import { LiveTrackingMap } from '../../components/LiveTrackingMap';
import { useLiveTracking } from '../../hooks/useLiveTracking';

export default function AdminPortal() {
  const { user } = useAuth();
  const [stats, setStats] = useState({
    warehouses: 0,
    vehicles: 0,
    drivers: 0,
    deliveries: 0,
  });
  const [deliveries, setDeliveries] = useState([]);
  const [selectedDeliveryId, setSelectedDeliveryId] = useState(null);
  const [loading, setLoading] = useState(true);

  const { trackingData, connectionStatus, refresh: refreshTracking } = useLiveTracking(
    selectedDeliveryId
  );

  const fetchSystemData = async () => {
    setLoading(true);
    try {
      const [whRes, vehRes, drvRes, delRes] = await Promise.allSettled([
        listWarehouses(),
        listVehicles(),
        listDrivers(),
        listDeliveries(),
      ]);

      const whList = whRes.status === 'fulfilled' ? whRes.value || [] : [];
      const vehList = vehRes.status === 'fulfilled' ? vehRes.value || [] : [];
      const drvList = drvRes.status === 'fulfilled' ? drvRes.value || [] : [];
      const delList = delRes.status === 'fulfilled' ? delRes.value || [] : [];

      setStats({
        warehouses: whList.length,
        vehicles: vehList.length,
        drivers: drvList.length,
        deliveries: delList.length,
      });

      setDeliveries(delList);
      if (delList.length > 0 && !selectedDeliveryId) {
        setSelectedDeliveryId(delList[0].id);
      }
    } catch (err) {
      console.warn('Error loading admin overview stats:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSystemData();
  }, []);

  return (
    <div className="max-w-7xl mx-auto px-6 py-8 space-y-6">
      {/* Header Bar */}
      <div className="flex flex-wrap items-center justify-between gap-4 pb-6 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-purple-500/10 text-purple-400 border border-purple-500/30 uppercase tracking-wider">
              Executive Command
            </span>
          </div>
          <h1 className="text-2xl font-extrabold text-white mt-1">Global Logistics & Fleet Operations</h1>
          <p className="text-xs text-slate-400">
            Administrator: <span className="text-slate-200 font-semibold">{user.full_name}</span> ({user.email})
          </p>
        </div>

        <button
          onClick={fetchSystemData}
          className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold border border-slate-700 flex items-center gap-2 transition"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh Fleet Telemetry</span>
        </button>
      </div>

      {/* KPI Overview Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-lg">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Active Hubs</span>
            <Warehouse className="w-4 h-4 text-indigo-400" />
          </div>
          <div className="text-3xl font-black text-white">{stats.warehouses}</div>
          <p className="text-[11px] text-slate-500 mt-1">Cross-docking facilities</p>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-lg">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Fleet Assets</span>
            <Truck className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-3xl font-black text-white">{stats.vehicles}</div>
          <p className="text-[11px] text-slate-500 mt-1">EVs, Vans, & Trucks</p>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-lg">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Active Drivers</span>
            <Users className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-3xl font-black text-white">{stats.drivers}</div>
          <p className="text-[11px] text-slate-500 mt-1">Verified & assigned crew</p>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-lg">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Total Deliveries</span>
            <Package className="w-4 h-4 text-purple-400" />
          </div>
          <div className="text-3xl font-black text-white">{stats.deliveries}</div>
          <p className="text-[11px] text-slate-500 mt-1">Dispatches in lifecycle</p>
        </div>
      </div>

      {/* Live Fleet Operations Command Center */}
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
    </div>
  );
}
