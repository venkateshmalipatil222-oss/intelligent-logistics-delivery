import React, { useState, useEffect } from 'react';
import {
  Warehouse,
  Package,
  Truck,
  CheckCircle2,
  Clock,
  Sparkles,
  RefreshCw,
  Send,
  AlertCircle,
  MapPin,
  ChevronRight,
  Filter,
  Layers,
  ArrowUpRight,
  Users,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import {
  listOrders,
  listWarehouses,
  listDrivers,
  updateOrderStatus,
  autoAssignDriver,
  getWarehouseUtilization,
} from '../../api/client';
import DriverRecommendationModal from '../../components/DriverRecommendationModal';

export default function WarehousePortal() {
  const { user } = useAuth();
  const [warehouses, setWarehouses] = useState([]);
  const [utilizationData, setUtilizationData] = useState(null);
  const [orders, setOrders] = useState([]);
  const [drivers, setDrivers] = useState([]);
  const [selectedQueue, setSelectedQueue] = useState('READY_FOR_DISPATCH'); // 'READY_FOR_DISPATCH' | 'PROCESSING' | 'ACTIVE_DISPATCHED'
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [successMessage, setSuccessMessage] = useState(null);
  const [errorMessage, setErrorMessage] = useState(null);

  // AI Recommendation Modal State
  const [modalOrder, setModalOrder] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const fetchWarehouseData = async () => {
    setLoading(true);
    setErrorMessage(null);
    try {
      const [whRes, utilRes, ordRes, drvRes] = await Promise.allSettled([
        listWarehouses(),
        getWarehouseUtilization(),
        listOrders(),
        listDrivers(),
      ]);

      if (whRes.status === 'fulfilled') setWarehouses(whRes.value || []);
      if (utilRes.status === 'fulfilled') setUtilizationData(utilRes.value);
      if (ordRes.status === 'fulfilled') setOrders(ordRes.value || []);
      if (drvRes.status === 'fulfilled') setDrivers(drvRes.value || []);
    } catch (err) {
      setErrorMessage(err.normalizedMessage || 'Failed to load warehouse operations data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchWarehouseData();
  }, []);

  // Filter orders by staging queues
  const readyOrders = orders.filter(
    (o) => o.status === 'READY_FOR_DISPATCH' || (o.package?.is_ready_for_dispatch && o.status === 'PROCESSING')
  );
  const processingOrders = orders.filter(
    (o) => o.status === 'PROCESSING' || o.status === 'CONFIRMED' || o.status === 'CREATED'
  );
  const activeDispatchedOrders = orders.filter(
    (o) => o.status === 'DISPATCHED' || o.status === 'IN_TRANSIT' || o.status === 'OUT_FOR_DELIVERY'
  );

  const availableDriversCount = drivers.filter((d) => d.status === 'AVAILABLE').length;

  const handleMarkReady = async (orderId) => {
    setActionLoading(true);
    setErrorMessage(null);
    try {
      await updateOrderStatus(orderId, {
        status: 'READY_FOR_DISPATCH',
        reason: 'Warehouse staging inspection completed and verified',
      });
      setSuccessMessage(`Order #${orderId} marked READY FOR DISPATCH on staging dock`);
      await fetchWarehouseData();
    } catch (err) {
      setErrorMessage(err.normalizedMessage || 'Failed to update order status');
    } finally {
      setActionLoading(false);
    }
  };

  const handleQuickAutoAssign = async (orderId) => {
    setActionLoading(true);
    setErrorMessage(null);
    try {
      const result = await autoAssignDriver(orderId);
      setSuccessMessage(
        `Order successfully auto-dispatched to ${result.assigned_driver_name} (OTP: ${result.otp_code})`
      );
      await fetchWarehouseData();
    } catch (err) {
      setErrorMessage(err.normalizedMessage || 'Failed to auto-assign driver');
    } finally {
      setActionLoading(false);
    }
  };

  const handleOpenAiModal = (order) => {
    setModalOrder(order);
    setIsModalOpen(true);
  };

  const handleDispatchSuccess = (result) => {
    setSuccessMessage(
      `Dispatched Order ${modalOrder?.order_number} to ${result.assigned_driver_name} (OTP: ${result.otp_code})`
    );
    fetchWarehouseData();
  };

  return (
    <div className="max-w-7xl mx-auto px-6 py-8 space-y-6">
      {/* Header Bar */}
      <div className="flex flex-wrap items-center justify-between gap-4 pb-6 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-blue-500/10 text-blue-400 border border-blue-500/30 uppercase tracking-wider">
              Warehouse Dispatch Center
            </span>
            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-purple-500/10 text-purple-400 border border-purple-500/30 uppercase tracking-wider">
              AI Staging Optimization
            </span>
          </div>
          <h1 className="text-2xl font-extrabold text-white mt-1">Cross-Docking & Package Dispatch Hub</h1>
          <p className="text-xs text-slate-400">
            Manager: <span className="text-slate-200 font-semibold">{user.full_name}</span> ({user.email})
          </p>
        </div>

        <button
          onClick={fetchWarehouseData}
          disabled={loading || actionLoading}
          className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold border border-slate-700 flex items-center gap-2 transition disabled:opacity-50 cursor-pointer"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh Staging Telemetry</span>
        </button>
      </div>

      {/* Notifications / Alerts */}
      {successMessage && (
        <div className="p-4 rounded-xl bg-emerald-950/60 border border-emerald-500/40 text-emerald-200 text-xs flex items-center justify-between animate-in fade-in">
          <div className="flex items-center space-x-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
            <span>{successMessage}</span>
          </div>
          <button onClick={() => setSuccessMessage(null)} className="text-emerald-400 hover:text-white font-bold ml-4">
            ✕
          </button>
        </div>
      )}

      {errorMessage && (
        <div className="p-4 rounded-xl bg-rose-950/60 border border-rose-500/40 text-rose-200 text-xs flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
            <span>{errorMessage}</span>
          </div>
          <button onClick={() => setErrorMessage(null)} className="text-rose-400 hover:text-white font-bold ml-4">
            ✕
          </button>
        </div>
      )}

      {/* KPI Overview Telemetry */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-lg">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Ready to Dispatch</span>
            <Package className="w-4 h-4 text-purple-400" />
          </div>
          <div className="text-3xl font-black text-white">{readyOrders.length}</div>
          <p className="text-[11px] text-purple-400 font-semibold mt-1">Staged on loading docks</p>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-lg">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">In Preparation</span>
            <Clock className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-3xl font-black text-white">{processingOrders.length}</div>
          <p className="text-[11px] text-slate-500 mt-1">Weighing & packing queue</p>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-lg">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Active Dispatches</span>
            <Truck className="w-4 h-4 text-blue-400" />
          </div>
          <div className="text-3xl font-black text-white">{activeDispatchedOrders.length}</div>
          <p className="text-[11px] text-slate-500 mt-1">Currently in transit</p>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-lg">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold uppercase tracking-wider">Available Drivers</span>
            <Users className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-3xl font-black text-white">{availableDriversCount}</div>
          <p className="text-[11px] text-emerald-400 font-semibold mt-1">Ready for pickup</p>
        </div>
      </div>

      {/* Facility Floor Capacity & Utilization Monitor */}
      {utilizationData && utilizationData.warehouses?.length > 0 && (
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 pb-3">
            <div className="flex items-center space-x-3">
              <div className="w-9 h-9 rounded-xl bg-blue-500/20 text-blue-400 flex items-center justify-center border border-blue-500/30">
                <Warehouse className="w-5 h-5" />
              </div>
              <div>
                <h2 className="text-base font-bold text-white">Facility Capacity & Floor Space Monitor</h2>
                <p className="text-xs text-slate-400">
                  Total network capacity: <span className="text-slate-200 font-bold">{utilizationData.total_network_capacity_sqft.toLocaleString()} sq ft</span> &bull; Average utilization: <span className="text-emerald-400 font-bold">{utilizationData.average_utilization_rate_pct}%</span>
                </p>
              </div>
            </div>
            <span className="px-3 py-1 rounded-full text-xs font-bold bg-slate-800 text-slate-300 border border-slate-700">
              {utilizationData.total_warehouses} Cross-Dock Facilities Active
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 pt-1">
            {utilizationData.warehouses.map((wh) => (
              <div
                key={wh.warehouse_id}
                className="p-4 rounded-xl bg-slate-950/70 border border-slate-800 space-y-3"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-sm font-bold text-white">{wh.warehouse_name}</h3>
                    <p className="text-[11px] text-slate-400 font-mono">
                      {wh.warehouse_code} &bull; {wh.city}, {wh.state}
                    </p>
                  </div>
                  <span
                    className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                      wh.status_level === 'CRITICAL'
                        ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                        : wh.status_level === 'ELEVATED'
                        ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                        : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                    }`}
                  >
                    {wh.status_level}
                  </span>
                </div>

                {/* Progress bar */}
                <div className="space-y-1">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-slate-400">Capacity Utilized</span>
                    <span className="font-bold text-white font-mono">{wh.utilization_rate_pct}%</span>
                  </div>
                  <div className="w-full h-2 bg-slate-800 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all duration-500 ${
                        wh.utilization_rate_pct >= 90
                          ? 'bg-rose-500'
                          : wh.utilization_rate_pct >= 70
                          ? 'bg-amber-500'
                          : 'bg-emerald-500'
                      }`}
                      style={{ width: `${Math.min(wh.utilization_rate_pct, 100)}%` }}
                    />
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-2 pt-2 border-t border-slate-800/80 text-[11px]">
                  <div>
                    <span className="text-slate-500 block">Staged</span>
                    <span className="text-purple-400 font-bold">{wh.staged_packages_count} pkgs</span>
                  </div>
                  <div>
                    <span className="text-slate-500 block">Processing</span>
                    <span className="text-amber-400 font-bold">{wh.processing_orders_count} ord</span>
                  </div>
                  <div>
                    <span className="text-slate-500 block">Available</span>
                    <span className="text-slate-300 font-mono font-bold">
                      {wh.available_capacity_sqft.toLocaleString()} sqft
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Package Staging & Dispatch Queue Section */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-5">
        {/* Queue Switcher Navigation */}
        <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 pb-4">
          <div className="flex items-center gap-2">
            <button
              onClick={() => setSelectedQueue('READY_FOR_DISPATCH')}
              className={`px-4 py-2 rounded-xl text-xs font-bold transition flex items-center gap-2 cursor-pointer ${
                selectedQueue === 'READY_FOR_DISPATCH'
                  ? 'bg-purple-600 text-white shadow-lg shadow-purple-500/20'
                  : 'bg-slate-950 text-slate-400 hover:text-white border border-slate-800'
              }`}
            >
              <Sparkles className="w-3.5 h-3.5" />
              <span>Ready for Dispatch ({readyOrders.length})</span>
            </button>

            <button
              onClick={() => setSelectedQueue('PROCESSING')}
              className={`px-4 py-2 rounded-xl text-xs font-bold transition flex items-center gap-2 cursor-pointer ${
                selectedQueue === 'PROCESSING'
                  ? 'bg-amber-600 text-white shadow-lg shadow-amber-500/20'
                  : 'bg-slate-950 text-slate-400 hover:text-white border border-slate-800'
              }`}
            >
              <Clock className="w-3.5 h-3.5" />
              <span>In Preparation Queue ({processingOrders.length})</span>
            </button>

            <button
              onClick={() => setSelectedQueue('ACTIVE_DISPATCHED')}
              className={`px-4 py-2 rounded-xl text-xs font-bold transition flex items-center gap-2 cursor-pointer ${
                selectedQueue === 'ACTIVE_DISPATCHED'
                  ? 'bg-blue-600 text-white shadow-lg shadow-blue-500/20'
                  : 'bg-slate-950 text-slate-400 hover:text-white border border-slate-800'
              }`}
            >
              <Truck className="w-3.5 h-3.5" />
              <span>Active on Road ({activeDispatchedOrders.length})</span>
            </button>
          </div>

          <span className="text-xs text-slate-400">
            Showing <b className="text-white">
              {selectedQueue === 'READY_FOR_DISPATCH'
                ? readyOrders.length
                : selectedQueue === 'PROCESSING'
                ? processingOrders.length
                : activeDispatchedOrders.length}
            </b> packages
          </span>
        </div>

        {/* Queue Items Table / Cards */}
        {selectedQueue === 'READY_FOR_DISPATCH' && (
          <div className="space-y-3">
            {readyOrders.length === 0 ? (
              <div className="py-12 text-center text-slate-500 text-xs">
                No orders currently waiting on loading docks. Incoming packages will appear here once prepped.
              </div>
            ) : (
              readyOrders.map((ord) => (
                <div
                  key={ord.id}
                  className="p-4 rounded-xl bg-slate-950/80 border border-purple-500/30 hover:border-purple-500/60 transition flex flex-wrap items-center justify-between gap-4"
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-mono font-bold text-white text-sm">{ord.order_number}</span>
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                          ord.priority === 'URGENT'
                            ? 'bg-rose-500/20 text-rose-300'
                            : ord.priority === 'HIGH'
                            ? 'bg-amber-500/20 text-amber-300'
                            : 'bg-slate-800 text-slate-300'
                        }`}
                      >
                        {ord.priority}
                      </span>
                      {ord.package?.tracking_number && (
                        <span className="text-xs font-mono text-slate-400">({ord.package.tracking_number})</span>
                      )}
                    </div>
                    <div className="text-xs text-slate-300 flex items-center gap-1">
                      <MapPin className="w-3.5 h-3.5 text-rose-400 shrink-0" />
                      <span>{ord.destination_address}, {ord.destination_city}</span>
                    </div>
                    <div className="text-[11px] text-slate-400 flex items-center gap-3">
                      <span>Weight: <b className="text-slate-200">{ord.package?.weight_kg || 1.0} kg</b></span>
                      <span>Est. Distance: <b className="text-slate-200">{ord.estimated_distance_km || 0} km</b></span>
                      <span>Est. Cost: <b className="text-slate-200">₹{ord.estimated_delivery_cost?.toFixed(2) || '0.00'}</b></span>
                    </div>
                  </div>

                  {/* Actions for Ready Order */}
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handleOpenAiModal(ord)}
                      className="px-3 py-2 rounded-xl bg-purple-500/20 hover:bg-purple-500/30 text-purple-300 border border-purple-500/40 text-xs font-bold flex items-center gap-1.5 transition cursor-pointer"
                    >
                      <Sparkles className="w-3.5 h-3.5" />
                      <span>AI Recommend</span>
                    </button>

                    <button
                      onClick={() => handleQuickAutoAssign(ord.id)}
                      disabled={actionLoading}
                      className="px-4 py-2 rounded-xl bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white text-xs font-bold shadow-lg shadow-purple-500/20 flex items-center gap-1.5 transition disabled:opacity-50 cursor-pointer"
                    >
                      <Send className="w-3.5 h-3.5" />
                      <span>1-Click Auto Dispatch</span>
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        )}

        {selectedQueue === 'PROCESSING' && (
          <div className="space-y-3">
            {processingOrders.length === 0 ? (
              <div className="py-12 text-center text-slate-500 text-xs">
                No orders in the preparation queue.
              </div>
            ) : (
              processingOrders.map((ord) => (
                <div
                  key={ord.id}
                  className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 hover:border-slate-700 transition flex flex-wrap items-center justify-between gap-4"
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-mono font-bold text-white text-sm">{ord.order_number}</span>
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/20 text-amber-300 uppercase">
                        {ord.status}
                      </span>
                    </div>
                    <div className="text-xs text-slate-300 flex items-center gap-1">
                      <MapPin className="w-3.5 h-3.5 text-rose-400 shrink-0" />
                      <span>{ord.destination_address}, {ord.destination_city}</span>
                    </div>
                    <div className="text-[11px] text-slate-400 flex items-center gap-3">
                      <span>Weight: <b className="text-slate-200">{ord.package?.weight_kg || 1.0} kg</b></span>
                      <span>Category: <b className="text-slate-200">{ord.package?.category || 'GENERAL'}</b></span>
                      {ord.package?.is_fragile && (
                        <span className="text-rose-400 font-semibold">&bull; FRAGILE</span>
                      )}
                    </div>
                  </div>

                  <button
                    onClick={() => handleMarkReady(ord.id)}
                    disabled={actionLoading}
                    className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold shadow-lg shadow-emerald-500/20 flex items-center gap-1.5 transition disabled:opacity-50 cursor-pointer"
                  >
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span>Mark Ready for Dispatch</span>
                  </button>
                </div>
              ))
            )}
          </div>
        )}

        {selectedQueue === 'ACTIVE_DISPATCHED' && (
          <div className="space-y-3">
            {activeDispatchedOrders.length === 0 ? (
              <div className="py-12 text-center text-slate-500 text-xs">
                No active dispatches currently on the road from this hub.
              </div>
            ) : (
              activeDispatchedOrders.map((ord) => (
                <div
                  key={ord.id}
                  className="p-4 rounded-xl bg-slate-950/80 border border-blue-500/30 transition flex flex-wrap items-center justify-between gap-4"
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-mono font-bold text-white text-sm">{ord.order_number}</span>
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-blue-500/20 text-blue-300 uppercase">
                        {ord.status}
                      </span>
                    </div>
                    <div className="text-xs text-slate-300 flex items-center gap-1">
                      <MapPin className="w-3.5 h-3.5 text-rose-400 shrink-0" />
                      <span>{ord.destination_address}, {ord.destination_city}</span>
                    </div>
                    <div className="text-[11px] text-slate-400">
                      Dispatched with live tracking active
                    </div>
                  </div>

                  <div className="text-right text-xs">
                    <span className="text-emerald-400 font-bold block">En Route</span>
                    <span className="text-slate-500 text-[10px]">Surveillance tracking online</span>
                  </div>
                </div>
              ))
            )}
          </div>
        )}
      </div>

      {/* AI Recommendation Modal */}
      <DriverRecommendationModal
        order={modalOrder}
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onDispatchSuccess={handleDispatchSuccess}
      />
    </div>
  );
}
