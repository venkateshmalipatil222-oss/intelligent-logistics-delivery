import React, { useState, useEffect } from 'react';
import {
  Package,
  MapPin,
  Clock,
  ShieldCheck,
  Search,
  Truck,
  CheckCircle2,
  AlertCircle,
  Radio,
  ChevronRight,
  ExternalLink,
  KeyRound,
  RefreshCw,
  Phone,
  Calendar,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { listOrders, trackShipment, regenerateDeliveryOTP } from '../../api/client';
import { LiveTrackingMap } from '../../components/LiveTrackingMap';
import { useLiveTracking } from '../../hooks/useLiveTracking';
import CustomerCostCalculator from '../../components/CustomerCostCalculator';

export default function CustomerPortal() {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState('tracking'); // 'tracking' | 'calculator'
  const [orders, setOrders] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [trackedShipment, setTrackedShipment] = useState(null);
  const [loading, setLoading] = useState(true);
  const [searchLoading, setSearchLoading] = useState(false);
  const [isRegeneratingOTP, setIsRegeneratingOTP] = useState(false);
  const [error, setError] = useState(null);

  // Active delivery ID for real-time map tracking
  const activeDeliveryId =
    trackedShipment?.delivery?.id ||
    selectedOrder?.delivery?.id ||
    (selectedOrder?.status === 'DISPATCHED' ? 1 : null); // Fallback to demo delivery 1 if dispatched

  const { trackingData, connectionStatus, refresh: refreshTracking } = useLiveTracking(
    activeDeliveryId
  );

  const fetchCustomerOrders = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await listOrders();
      const list = data || [];
      setOrders(list);

      // Auto-track the first order with an active status or first order in list
      if (list.length > 0 && !selectedOrder) {
        const firstOrder = list[0];
        setSelectedOrder(firstOrder);
        loadShipmentTracking(firstOrder.order_number);
      }
    } catch (err) {
      setError(err.normalizedMessage || 'Failed to load your orders');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCustomerOrders();
  }, []);

  const loadShipmentTracking = async (orderOrTrackingNum) => {
    if (!orderOrTrackingNum) return;
    setSearchLoading(true);
    setError(null);
    try {
      const trackingDetails = await trackShipment(orderOrTrackingNum);
      setTrackedShipment(trackingDetails);
    } catch (err) {
      setError(err.normalizedMessage || `Shipment '${orderOrTrackingNum}' not found`);
    } finally {
      setSearchLoading(false);
    }
  };

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;
    loadShipmentTracking(searchQuery.trim());
  };

  const handleOrderSelect = (order) => {
    setSelectedOrder(order);
    loadShipmentTracking(order.order_number);
  };

  const handleRegenerateOTP = async () => {
    const delId = trackedShipment?.delivery?.id || activeDeliveryId;
    if (!delId) return;
    setIsRegeneratingOTP(true);
    try {
      const res = await regenerateDeliveryOTP(delId);
      setTrackedShipment((prev) => ({
        ...prev,
        delivery: {
          ...prev.delivery,
          otp_code: res.otp_code,
        },
      }));
    } catch (err) {
      setError(err.normalizedMessage || 'Failed to regenerate OTP');
    } finally {
      setIsRegeneratingOTP(false);
    }
  };

  // Milestone timeline stages
  const statusMilestones = [
    { key: 'PENDING', label: 'Order Placed' },
    { key: 'PROCESSING', label: 'Staged & Packed' },
    { key: 'DISPATCHED', label: 'Dispatched Hub' },
    { key: 'IN_TRANSIT', label: 'In Transit' },
    { key: 'DELIVERED', label: 'Delivered' },
  ];

  const getStepStatus = (stepKey, currentStatus) => {
    const sequence = [
      'PENDING',
      'CONFIRMED',
      'PROCESSING',
      'READY_FOR_DISPATCH',
      'DISPATCHED',
      'IN_TRANSIT',
      'OUT_FOR_DELIVERY',
      'DELIVERED',
    ];

    const stepIndex = sequence.indexOf(stepKey);
    const currentIndex = sequence.indexOf(currentStatus);

    if (currentIndex >= stepIndex) return 'COMPLETED';
    if (currentIndex + 1 === stepIndex) return 'CURRENT';
    return 'UPCOMING';
  };

  return (
    <div className="max-w-7xl mx-auto px-6 py-8 space-y-6">
      {/* Header Bar */}
      <div className="flex flex-wrap items-center justify-between gap-4 pb-6 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 uppercase tracking-wider">
              Customer Tracking Center
            </span>
          </div>
          <h1 className="text-2xl font-extrabold text-white mt-1">Shipment Tracking & Order Center</h1>
          <p className="text-xs text-slate-400">
            Account: <span className="text-slate-200 font-semibold">{user.full_name}</span> ({user.email})
          </p>
        </div>

        {/* Search Bar for Instant Tracking */}
        <form onSubmit={handleSearchSubmit} className="flex items-center gap-2">
          <div className="relative">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Track by ORD or TRK number..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9 pr-4 py-2 bg-slate-900 border border-slate-700 rounded-xl text-white text-xs placeholder-slate-500 focus:outline-none focus:border-indigo-500 w-64 md:w-80"
            />
          </div>
          <button
            type="submit"
            disabled={searchLoading}
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-semibold transition disabled:opacity-50"
          >
            {searchLoading ? 'Searching...' : 'Track'}
          </button>
        </form>
      </div>

      {/* Portal Navigation Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-800 pb-2">
        <button
          onClick={() => setActiveTab('tracking')}
          className={`px-4 py-2 rounded-xl text-xs font-bold transition flex items-center gap-2 cursor-pointer ${
            activeTab === 'tracking'
              ? 'bg-emerald-600 text-white shadow-lg shadow-emerald-500/20'
              : 'bg-slate-900 text-slate-400 hover:text-white hover:bg-slate-800 border border-slate-800'
          }`}
        >
          <Radio className="w-3.5 h-3.5" />
          <span>Live Tracking & Orders</span>
        </button>

        <button
          onClick={() => setActiveTab('calculator')}
          className={`px-4 py-2 rounded-xl text-xs font-bold transition flex items-center gap-2 cursor-pointer ${
            activeTab === 'calculator'
              ? 'bg-emerald-600 text-white shadow-lg shadow-emerald-500/20'
              : 'bg-slate-900 text-slate-400 hover:text-white hover:bg-slate-800 border border-slate-800'
          }`}
        >
          <Package className="w-3.5 h-3.5" />
          <span>Transparent Cost Calculator</span>
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

      {/* Tab 1: Live Tracking & Orders */}
      {activeTab === 'tracking' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column: Your Orders List */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h2 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <Package className="w-4 h-4 text-emerald-400" />
              <span>Your Orders ({orders.length})</span>
            </h2>
            <button
              onClick={fetchCustomerOrders}
              className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition"
              title="Refresh Orders"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            </button>
          </div>

          {orders.length === 0 ? (
            <div className="text-center py-10 text-slate-500 text-xs">
              <Package className="w-8 h-8 mx-auto mb-2 opacity-40 text-slate-400" />
              No orders found. Your placed orders will appear here automatically.
            </div>
          ) : (
            <div className="space-y-3 max-h-[540px] overflow-y-auto pr-1">
              {orders.map((ord) => {
                const isSelected =
                  selectedOrder?.order_number === ord.order_number ||
                  trackedShipment?.order_number === ord.order_number;

                return (
                  <div
                    key={ord.id}
                    onClick={() => handleOrderSelect(ord)}
                    className={`p-3.5 rounded-xl border transition cursor-pointer ${
                      isSelected
                        ? 'bg-indigo-600/10 border-indigo-500/40 text-white shadow-md'
                        : 'bg-slate-950/60 border-slate-800/80 hover:border-slate-700 text-slate-300'
                    }`}
                  >
                    <div className="flex items-center justify-between text-xs mb-1.5">
                      <span className="font-mono font-bold text-slate-100">{ord.order_number}</span>
                      <span
                        className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase ${
                          ord.status === 'DELIVERED'
                            ? 'bg-emerald-500/20 text-emerald-400'
                            : ord.status === 'DISPATCHED' || ord.status === 'IN_TRANSIT'
                            ? 'bg-amber-500/20 text-amber-400'
                            : 'bg-slate-800 text-slate-300'
                        }`}
                      >
                        {ord.status}
                      </span>
                    </div>

                    <div className="text-xs text-slate-400 flex items-center gap-1 truncate mb-2">
                      <MapPin className="w-3 h-3 text-rose-400 shrink-0" />
                      <span className="truncate">{ord.destination_address}</span>
                    </div>

                    <div className="pt-2 border-t border-slate-800/60 flex items-center justify-between text-[11px] text-slate-500">
                      <span>Est. ₹{ord.estimated_delivery_cost?.toFixed(2) || '0.00'}</span>
                      <span className="text-indigo-400 font-medium flex items-center gap-0.5">
                        Track Live <ChevronRight className="w-3 h-3" />
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Right 2 Columns: Live Map & Delivery Milestone Details */}
        <div className="lg:col-span-2 space-y-6">
          {trackedShipment ? (
            <>
              {/* Order Status Progress Bar */}
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-5">
                <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 pb-4">
                  <div>
                    <span className="text-[10px] font-bold text-emerald-400 uppercase tracking-wider">
                      Tracking Reference
                    </span>
                    <h2 className="text-xl font-extrabold text-white mt-0.5 flex items-center gap-2">
                      <span>{trackedShipment.order_number}</span>
                      {trackedShipment.tracking_number && (
                        <span className="text-xs font-mono font-normal text-slate-400">
                          ({trackedShipment.tracking_number})
                        </span>
                      )}
                    </h2>
                  </div>

                  {/* Estimated Delivery Time or Destination Badge */}
                  <div className="text-right">
                    <span className="text-[10px] uppercase font-bold text-slate-400">Destination</span>
                    <div className="text-sm font-semibold text-white">
                      {trackedShipment.destination_city}, {trackedShipment.destination_postal_code}
                    </div>
                  </div>
                </div>

                {/* Milestone Stepper */}
                <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 pt-2">
                  {statusMilestones.map((milestone, idx) => {
                    const stepStatus = getStepStatus(milestone.key, trackedShipment.status);
                    const isDone = stepStatus === 'COMPLETED';
                    const isCurrent = stepStatus === 'CURRENT';

                    return (
                      <div key={milestone.key} className="space-y-1.5 text-center">
                        <div
                          className={`w-8 h-8 mx-auto rounded-full flex items-center justify-center text-xs font-bold transition ${
                            isDone
                              ? 'bg-emerald-500 text-white shadow-lg shadow-emerald-500/20'
                              : isCurrent
                              ? 'bg-amber-500 text-white animate-pulse'
                              : 'bg-slate-800 text-slate-500'
                          }`}
                        >
                          {isDone ? '✓' : idx + 1}
                        </div>
                        <div
                          className={`text-xs font-semibold ${
                            isDone ? 'text-emerald-400' : isCurrent ? 'text-amber-400' : 'text-slate-500'
                          }`}
                        >
                          {milestone.label}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Delivery Security OTP Card & Driver Contact (if dispatched) */}
              {trackedShipment.delivery && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Customer Security OTP Card */}
                  <div className="bg-gradient-to-br from-emerald-950/60 to-slate-900 border border-emerald-500/40 rounded-2xl p-5 shadow-lg space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-emerald-400 uppercase tracking-wider flex items-center gap-1.5">
                        <KeyRound className="w-4 h-4" />
                        Delivery Security Verification
                      </span>
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/20 text-emerald-300">
                        Drop-off Protection
                      </span>
                    </div>

                    <div className="text-center py-2 bg-slate-950/80 rounded-xl border border-emerald-500/30">
                      <div className="text-[10px] text-slate-400 uppercase tracking-widest font-semibold">
                        Your Verification OTP
                      </div>
                      <div className="text-3xl font-black text-emerald-400 font-mono tracking-widest mt-1">
                        {trackedShipment.delivery.otp_code || '------'}
                      </div>
                    </div>

                    <div className="flex flex-wrap items-center justify-between gap-2 pt-1">
                      <p className="text-[11px] text-slate-400 leading-relaxed flex-1">
                        Hand this 6-digit code to the delivery driver only after inspecting and receiving your package.
                      </p>
                      {trackedShipment.delivery.status !== 'DELIVERED' && (
                        <button
                          onClick={handleRegenerateOTP}
                          disabled={isRegeneratingOTP}
                          className="px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-emerald-400 border border-slate-700 text-xs font-semibold flex items-center gap-1.5 transition shrink-0 cursor-pointer disabled:opacity-50"
                        >
                          <RefreshCw className={`w-3 h-3 ${isRegeneratingOTP ? 'animate-spin' : ''}`} />
                          <span>Regenerate OTP</span>
                        </button>
                      )}
                    </div>
                  </div>

                  {/* Driver & Vehicle Card */}
                  <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-lg space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
                        <Truck className="w-4 h-4 text-indigo-400" />
                        Assigned Fleet Driver
                      </span>
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-indigo-500/20 text-indigo-300">
                        Active Delivery
                      </span>
                    </div>

                    <div className="space-y-1 text-xs">
                      <div className="text-base font-bold text-white">
                        {trackedShipment.delivery.driver_name || 'Fleet Driver'}
                      </div>
                      {trackedShipment.delivery.vehicle_registration && (
                        <div className="text-slate-400 font-mono">
                          Vehicle: <span className="text-slate-200">{trackedShipment.delivery.vehicle_registration}</span>
                        </div>
                      )}
                      {trackedShipment.delivery.driver_phone && (
                        <div className="text-slate-400 flex items-center gap-1.5 pt-1">
                          <Phone className="w-3.5 h-3.5 text-slate-400" />
                          <span>{trackedShipment.delivery.driver_phone}</span>
                        </div>
                      )}
                    </div>

                    <div className="text-[11px] text-slate-500 pt-1 border-t border-slate-800">
                      Delivery Reference: <b className="text-slate-300 font-mono">{trackedShipment.delivery.delivery_number}</b>
                    </div>
                  </div>
                </div>
              )}

              {/* Interactive OpenStreetMap Live Tracking Map */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-2">
                    <Radio className="w-3.5 h-3.5 text-emerald-400 animate-pulse" />
                    <span>Real-Time Driver Location & Dynamic ETA</span>
                  </h3>
                </div>
                <LiveTrackingMap
                  trackingData={trackingData}
                  connectionStatus={connectionStatus}
                  onRefresh={refreshTracking}
                />
              </div>
            </>
          ) : (
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-16 text-center text-slate-500 text-xs">
              Select an order from your list or enter an order number above to track in real time.
            </div>
          )}
        </div>
      </div>
      )}

      {/* Tab 2: Cost Estimator */}
      {activeTab === 'calculator' && (
        <CustomerCostCalculator />
      )}
    </div>
  );
}
