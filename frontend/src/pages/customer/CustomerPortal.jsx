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
  PlusCircle,
  Building2,
  Sparkles,
  Send,
  Coins,
  MessageSquare,
  Smartphone,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { listOrders, trackShipment, regenerateDeliveryOTP, createOrder, listWarehouses } from '../../api/client';
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
  const [isOmnichannelModalOpen, setIsOmnichannelModalOpen] = useState(false);
  const [error, setError] = useState(null);

  const [warehouses, setWarehouses] = useState([]);
  const [bookingLoading, setBookingLoading] = useState(false);
  const [bookingSuccess, setBookingSuccess] = useState(null);

  // New Booking State (From Location A -> Location B)
  const [bookingForm, setBookingForm] = useState({
    warehouse_id: 1,
    destination_address: 'Tech Park, Electronic City Phase 1',
    destination_city: 'Bengaluru',
    destination_state: 'Karnataka',
    destination_postal_code: '560100',
    destination_latitude: 12.8452,
    destination_longitude: 77.6602,
    priority: 'MEDIUM',
    delivery_slot: 'MORNING',
    weight_kg: 2.5,
    length_cm: 25,
    width_cm: 18,
    height_cm: 12,
    category: 'ELECTRONICS',
    is_fragile: false,
    requires_cold_storage: false,
  });

  const destinationPresets = [
    { label: 'Electronic City Phase 1 (BLR)', address: 'Infosys Main Gate, Electronic City Phase 1', city: 'Bengaluru', state: 'Karnataka', postal: '560100', lat: 12.8452, lon: 77.6602 },
    { label: 'Whitefield ITPL (BLR)', address: 'ITPB Main Road, Whitefield', city: 'Bengaluru', state: 'Karnataka', postal: '560066', lat: 12.9840, lon: 77.7499 },
    { label: 'Koramangala 5th Block (BLR)', address: '80ft Road, Koramangala 5th Block', city: 'Bengaluru', state: 'Karnataka', postal: '560095', lat: 12.9352, lon: 77.6245 },
    { label: 'Indiranagar 100ft Rd (BLR)', address: '12th Main Rd, Indiranagar', city: 'Bengaluru', state: 'Karnataka', postal: '560038', lat: 12.9784, lon: 77.6408 },
    { label: 'BKC Financial Center (BOM)', address: 'G Block, Bandra Kurla Complex', city: 'Mumbai', state: 'Maharashtra', postal: '400051', lat: 19.0657, lon: 72.8687 },
    { label: 'Cyber City Gurugram (DEL)', address: 'Building 10, DLF Cyber City', city: 'Gurugram', state: 'Haryana', postal: '122002', lat: 28.4950, lon: 77.0895 },
    { label: 'Hitec City Cyber Towers (HYD)', address: 'Cyber Towers, Hitec City', city: 'Hyderabad', state: 'Telangana', postal: '500081', lat: 17.4435, lon: 78.3772 },
  ];

  const handlePresetSelect = (preset) => {
    setBookingForm((prev) => ({
      ...prev,
      destination_address: preset.address,
      destination_city: preset.city,
      destination_state: preset.state,
      destination_postal_code: preset.postal,
      destination_latitude: preset.lat,
      destination_longitude: preset.lon,
    }));
  };

  // Live Haversine Distance & Estimated Cost
  const selectedWarehouse = warehouses.find((w) => w.id === Number(bookingForm.warehouse_id)) || warehouses[0];
  const calculatedDistanceKm = (() => {
    if (!selectedWarehouse?.latitude || !bookingForm.destination_latitude) return 0;
    const R = 6371;
    const dLat = ((bookingForm.destination_latitude - selectedWarehouse.latitude) * Math.PI) / 180;
    const dLon = ((bookingForm.destination_longitude - selectedWarehouse.longitude) * Math.PI) / 180;
    const a =
      Math.sin(dLat / 2) ** 2 +
      Math.cos((selectedWarehouse.latitude * Math.PI) / 180) *
        Math.cos((bookingForm.destination_latitude * Math.PI) / 180) *
        Math.sin(dLon / 2) ** 2;
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return Math.round(R * c * 10) / 10;
  })();

  const estimatedBookingCost = Math.round(
    50 + calculatedDistanceKm * 12 + Number(bookingForm.weight_kg || 1) * 5
  );

  const fetchWarehouses = async () => {
    try {
      const data = await listWarehouses();
      const list = data || [];
      setWarehouses(list);
      if (list.length > 0 && !bookingForm.warehouse_id) {
        setBookingForm((prev) => ({ ...prev, warehouse_id: list[0].id }));
      }
    } catch (err) {
      console.error('Failed to load warehouses', err);
    }
  };

  const handleBookingSubmit = async (e) => {
    e.preventDefault();
    setBookingLoading(true);
    setError(null);
    setBookingSuccess(null);

    try {
      const payload = {
        warehouse_id: Number(bookingForm.warehouse_id),
        destination_address: bookingForm.destination_address,
        destination_city: bookingForm.destination_city,
        destination_state: bookingForm.destination_state,
        destination_postal_code: bookingForm.destination_postal_code,
        destination_latitude: Number(bookingForm.destination_latitude),
        destination_longitude: Number(bookingForm.destination_longitude),
        priority: bookingForm.priority,
        package: {
          weight_kg: Number(bookingForm.weight_kg),
          length_cm: Number(bookingForm.length_cm),
          width_cm: Number(bookingForm.width_cm),
          height_cm: Number(bookingForm.height_cm),
          category: bookingForm.category,
          is_fragile: bookingForm.is_fragile,
          requires_cold_storage: bookingForm.requires_cold_storage,
        },
      };

      const newOrder = await createOrder(payload);
      setBookingSuccess(newOrder);

      // Refresh orders list and select the new order
      await fetchCustomerOrders();
      setSelectedOrder(newOrder);
      if (newOrder.order_number) {
        loadShipmentTracking(newOrder.order_number);
      }
    } catch (err) {
      setError(err.normalizedMessage || 'Failed to book delivery ride');
    } finally {
      setBookingLoading(false);
    }
  };

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
    fetchWarehouses();
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
          onClick={() => setActiveTab('book')}
          className={`px-4 py-2 rounded-xl text-xs font-bold transition flex items-center gap-2 cursor-pointer ${
            activeTab === 'book'
              ? 'bg-emerald-600 text-white shadow-lg shadow-emerald-500/20'
              : 'bg-slate-900 text-slate-400 hover:text-white hover:bg-slate-800 border border-slate-800'
          }`}
        >
          <PlusCircle className="w-3.5 h-3.5" />
          <span>Book New Delivery / Ride</span>
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
                      <div className="flex items-center gap-2">
                        <button
                          type="button"
                          onClick={() => setIsOmnichannelModalOpen(true)}
                          className="px-3 py-1.5 rounded-xl bg-emerald-950/60 hover:bg-emerald-900/60 text-emerald-300 border border-emerald-500/30 text-xs font-semibold flex items-center gap-1.5 transition shrink-0 cursor-pointer"
                        >
                          <Smartphone className="w-3.5 h-3.5 text-emerald-400" />
                          <span>SMS & WhatsApp Alerts</span>
                        </button>

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

              {/* Phase 10: Omnichannel WhatsApp & SMS Notification Preview Modal */}
              {isOmnichannelModalOpen && (
                <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
                  <div className="bg-slate-900 border border-slate-700 rounded-3xl max-w-lg w-full p-6 shadow-2xl space-y-5 animate-in fade-in zoom-in-95 duration-200">
                    <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                      <div className="flex items-center gap-2.5">
                        <div className="w-8 h-8 rounded-xl bg-emerald-500/20 text-emerald-400 flex items-center justify-center">
                          <Smartphone className="w-4 h-4" />
                        </div>
                        <div>
                          <h3 className="text-sm font-bold text-white">Omnichannel Live Alerts</h3>
                          <p className="text-[11px] text-slate-400">Phase 10: WhatsApp Business & SMS Gateways</p>
                        </div>
                      </div>
                      <button
                        onClick={() => setIsOmnichannelModalOpen(false)}
                        className="text-slate-400 hover:text-white p-1 rounded-lg bg-slate-800"
                      >
                        ✕
                      </button>
                    </div>

                    <div className="space-y-4">
                      {/* WhatsApp Card */}
                      <div className="bg-[#0b141a] border border-[#202c33] rounded-2xl p-4 space-y-2">
                        <div className="flex items-center justify-between text-xs text-[#25d366]">
                          <span className="font-bold flex items-center gap-1">
                            <span>WhatsApp Business API</span>
                            <CheckCircle2 className="w-3.5 h-3.5 fill-[#25d366] text-black" />
                          </span>
                          <span className="text-[10px] text-slate-400">ILDO Logistics Official</span>
                        </div>
                        <div className="bg-[#005c4b] text-white p-3.5 rounded-2xl rounded-tl-none text-xs leading-relaxed shadow space-y-2">
                          <p>
                            📦 <b>Your delivery is out with driver {trackedShipment?.delivery?.driver_name || 'Rajesh Kumar'}!</b>
                          </p>
                          <p className="text-slate-100">
                            Vehicle: <b>{trackedShipment?.delivery?.vehicle_registration || 'KA-01-EV-2024'}</b>
                            <br />
                            Destination: {selectedOrder?.destination_address || 'Customer Location'}
                          </p>
                          <div className="bg-[#00473a] p-2 rounded-xl text-center font-mono text-sm tracking-widest font-black text-amber-300">
                            OTP: {trackedShipment?.delivery?.otp_code || '482910'}
                          </div>
                          <p className="text-[10px] text-emerald-200 opacity-90 text-right">
                            Just now &bull; ✓✓ Delivered
                          </p>
                        </div>
                      </div>

                      {/* SMS Text Message Card */}
                      <div className="bg-slate-950 border border-slate-800 rounded-2xl p-4 space-y-2">
                        <div className="flex items-center justify-between text-xs text-indigo-400 font-bold">
                          <span>SMS Gateway (Twilio / AWS SNS)</span>
                          <span className="text-[10px] text-slate-500 font-mono">From: ILDO-OTP</span>
                        </div>
                        <div className="bg-slate-900 border border-slate-800 p-3 rounded-xl text-xs text-slate-200 leading-relaxed font-sans">
                          ILDO: Your driver is within 100m geofence! Please inspect parcel and share OTP{' '}
                          <b className="font-mono text-white">{trackedShipment?.delivery?.otp_code || '482910'}</b> to authenticate handover.
                        </div>
                      </div>
                    </div>

                    <div className="flex justify-end pt-2">
                      <button
                        onClick={() => setIsOmnichannelModalOpen(false)}
                        className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold"
                      >
                        Close Preview
                      </button>
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

      {/* Tab 2: Book New Delivery (Point A -> Point B) */}
      {activeTab === 'book' && (
        <form onSubmit={handleBookingSubmit} className="space-y-6">
          {bookingSuccess && (
            <div className="p-5 rounded-2xl bg-emerald-950/60 border border-emerald-500/40 text-emerald-200 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 shadow-xl">
              <div className="flex items-start gap-3">
                <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />
                <div>
                  <h4 className="font-bold text-sm text-white">Delivery Order Successfully Created!</h4>
                  <p className="text-xs text-emerald-300/90 mt-0.5">
                    Order Ref: <span className="font-mono font-bold text-white">{bookingSuccess.order_number}</span> &bull;{' '}
                    Tracking Code: <span className="font-mono font-bold text-white">{bookingSuccess.package?.tracking_number}</span>
                  </p>
                  <p className="text-[11px] text-emerald-400/80 mt-1">
                    Your order has entered the warehouse staging queue and is ready for driver assignment.
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => {
                  setActiveTab('tracking');
                  setBookingSuccess(null);
                }}
                className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold transition shrink-0 cursor-pointer shadow-md shadow-emerald-600/30"
              >
                Track Live on Map →
              </button>
            </div>
          )}

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            {/* Left 7 Columns: Origin & Destination Locations */}
            <div className="lg:col-span-7 space-y-6">
              {/* Point A: Origin / Pickup Hub */}
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
                <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                  <div className="flex items-center space-x-2.5">
                    <div className="w-8 h-8 rounded-lg bg-indigo-500/20 text-indigo-400 flex items-center justify-center border border-indigo-500/30 font-bold text-xs">
                      A
                    </div>
                    <div>
                      <h3 className="text-sm font-bold text-white">Origin Location (Pickup Hub)</h3>
                      <p className="text-[11px] text-slate-400">Select source logistics warehouse or staging center</p>
                    </div>
                  </div>
                  <Building2 className="w-4 h-4 text-indigo-400" />
                </div>

                <div className="space-y-3">
                  <div>
                    <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                      Origin Warehouse / Distribution Hub
                    </label>
                    <select
                      value={bookingForm.warehouse_id}
                      onChange={(e) => setBookingForm({ ...bookingForm, warehouse_id: Number(e.target.value) })}
                      className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3.5 py-2.5 text-xs text-white focus:outline-none focus:border-indigo-500 font-medium"
                    >
                      {warehouses.map((wh) => (
                        <option key={wh.id} value={wh.id}>
                          {wh.name} &bull; {wh.city} ({wh.latitude.toFixed(4)}, {wh.longitude.toFixed(4)})
                        </option>
                      ))}
                    </select>
                  </div>

                  {selectedWarehouse && (
                    <div className="p-3 rounded-xl bg-slate-950/70 border border-slate-800 text-xs flex items-center justify-between text-slate-400">
                      <div>
                        <span className="text-white font-semibold">{selectedWarehouse.name}</span>
                        <div className="text-[11px] text-slate-500">{selectedWarehouse.address}, {selectedWarehouse.city}</div>
                      </div>
                      <div className="text-right font-mono text-[11px] text-indigo-300">
                        {selectedWarehouse.latitude.toFixed(4)}° N, {selectedWarehouse.longitude.toFixed(4)}° E
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Point B: Destination / Drop-off Location */}
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
                <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                  <div className="flex items-center space-x-2.5">
                    <div className="w-8 h-8 rounded-lg bg-rose-500/20 text-rose-400 flex items-center justify-center border border-rose-500/30 font-bold text-xs">
                      B
                    </div>
                    <div>
                      <h3 className="text-sm font-bold text-white">Destination Location (Drop-off)</h3>
                      <p className="text-[11px] text-slate-400">Enter delivery address and geographical drop coordinates</p>
                    </div>
                  </div>
                  <MapPin className="w-4 h-4 text-rose-400" />
                </div>

                {/* Quick Presets */}
                <div>
                  <span className="block text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-2">
                    Quick-Select Destination Hubs
                  </span>
                  <div className="flex flex-wrap gap-2">
                    {destinationPresets.map((preset, idx) => (
                      <button
                        key={idx}
                        type="button"
                        onClick={() => handlePresetSelect(preset)}
                        className="px-2.5 py-1 rounded-lg bg-slate-950 hover:bg-slate-800 text-slate-300 border border-slate-800 text-[11px] font-medium transition cursor-pointer hover:border-slate-700"
                      >
                        {preset.label}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="space-y-3">
                  <div>
                    <label className="block text-xs font-semibold text-slate-300 mb-1">
                      Street Address
                    </label>
                    <input
                      type="text"
                      required
                      value={bookingForm.destination_address}
                      onChange={(e) => setBookingForm({ ...bookingForm, destination_address: e.target.value })}
                      placeholder="Flat / Building, Street, Landmark"
                      className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3.5 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                    />
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                    <div>
                      <label className="block text-xs font-semibold text-slate-300 mb-1">City</label>
                      <input
                        type="text"
                        required
                        value={bookingForm.destination_city}
                        onChange={(e) => setBookingForm({ ...bookingForm, destination_city: e.target.value })}
                        className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-semibold text-slate-300 mb-1">State</label>
                      <input
                        type="text"
                        required
                        value={bookingForm.destination_state}
                        onChange={(e) => setBookingForm({ ...bookingForm, destination_state: e.target.value })}
                        className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-semibold text-slate-300 mb-1">Postal Code</label>
                      <input
                        type="text"
                        required
                        value={bookingForm.destination_postal_code}
                        onChange={(e) => setBookingForm({ ...bookingForm, destination_postal_code: e.target.value })}
                        className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-3 pt-1">
                    <div>
                      <label className="block text-[11px] font-semibold text-slate-400 mb-1">
                        Latitude (°N)
                      </label>
                      <input
                        type="number"
                        step="0.0001"
                        required
                        value={bookingForm.destination_latitude}
                        onChange={(e) => setBookingForm({ ...bookingForm, destination_latitude: Number(e.target.value) })}
                        className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white font-mono focus:outline-none focus:border-indigo-500"
                      />
                    </div>
                    <div>
                      <label className="block text-[11px] font-semibold text-slate-400 mb-1">
                        Longitude (°E)
                      </label>
                      <input
                        type="number"
                        step="0.0001"
                        required
                        value={bookingForm.destination_longitude}
                        onChange={(e) => setBookingForm({ ...bookingForm, destination_longitude: Number(e.target.value) })}
                        className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white font-mono focus:outline-none focus:border-indigo-500"
                      />
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Right 5 Columns: Package Specifications & Pricing */}
            <div className="lg:col-span-5 space-y-6">
              {/* Package Specs */}
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
                <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                  <h3 className="text-sm font-bold text-white flex items-center gap-2">
                    <Package className="w-4 h-4 text-emerald-400" />
                    <span>Package Details</span>
                  </h3>
                  <span className="text-[10px] font-mono text-slate-500 uppercase">Cargo Payload</span>
                </div>

                <div className="space-y-3">
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-xs font-semibold text-slate-300 mb-1">Weight (kg)</label>
                      <input
                        type="number"
                        step="0.1"
                        min="0.1"
                        required
                        value={bookingForm.weight_kg}
                        onChange={(e) => setBookingForm({ ...bookingForm, weight_kg: Number(e.target.value) })}
                        className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white font-mono focus:outline-none focus:border-indigo-500"
                      />
                    </div>

                    <div>
                      <label className="block text-xs font-semibold text-slate-300 mb-1">Category</label>
                      <select
                        value={bookingForm.category}
                        onChange={(e) => setBookingForm({ ...bookingForm, category: e.target.value })}
                        className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
                      >
                        <option value="ELECTRONICS">Electronics</option>
                        <option value="HEALTHCARE">Healthcare</option>
                        <option value="DOCUMENTS">Documents</option>
                        <option value="RETAIL">Retail Parcel</option>
                        <option value="PERISHABLE">Perishable</option>
                        <option value="GENERAL">General Goods</option>
                      </select>
                    </div>
                  </div>

                  <div className="grid grid-cols-3 gap-2">
                    <div>
                      <label className="block text-[10px] text-slate-400 mb-1">Length (cm)</label>
                      <input
                        type="number"
                        min="1"
                        value={bookingForm.length_cm}
                        onChange={(e) => setBookingForm({ ...bookingForm, length_cm: Number(e.target.value) })}
                        className="w-full bg-slate-950 border border-slate-700 rounded-xl px-2 py-1.5 text-xs text-white font-mono text-center"
                      />
                    </div>
                    <div>
                      <label className="block text-[10px] text-slate-400 mb-1">Width (cm)</label>
                      <input
                        type="number"
                        min="1"
                        value={bookingForm.width_cm}
                        onChange={(e) => setBookingForm({ ...bookingForm, width_cm: Number(e.target.value) })}
                        className="w-full bg-slate-950 border border-slate-700 rounded-xl px-2 py-1.5 text-xs text-white font-mono text-center"
                      />
                    </div>
                    <div>
                      <label className="block text-[10px] text-slate-400 mb-1">Height (cm)</label>
                      <input
                        type="number"
                        min="1"
                        value={bookingForm.height_cm}
                        onChange={(e) => setBookingForm({ ...bookingForm, height_cm: Number(e.target.value) })}
                        className="w-full bg-slate-950 border border-slate-700 rounded-xl px-2 py-1.5 text-xs text-white font-mono text-center"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-slate-300 mb-1.5 flex items-center justify-between">
                      <span>Scheduled Delivery Window (Phase 10)</span>
                      <span className="text-[10px] text-emerald-400 font-bold uppercase">Time-Slot</span>
                    </label>
                    <div className="grid grid-cols-3 gap-2">
                      {[
                        { id: 'MORNING', label: 'Morning Slot', time: '09:00 - 13:00' },
                        { id: 'AFTERNOON', label: 'Afternoon Slot', time: '13:00 - 17:00' },
                        { id: 'EVENING', label: 'Evening Slot', time: '17:00 - 21:00' },
                      ].map((slot) => (
                        <button
                          key={slot.id}
                          type="button"
                          onClick={() => setBookingForm({ ...bookingForm, delivery_slot: slot.id })}
                          className={`py-1.5 px-1 rounded-lg text-xs font-medium transition cursor-pointer border text-center ${
                            bookingForm.delivery_slot === slot.id
                              ? 'bg-emerald-600 text-white border-emerald-500 shadow-md font-bold'
                              : 'bg-slate-950 text-slate-400 border-slate-800 hover:bg-slate-800'
                          }`}
                        >
                          <div className="text-[11px]">{slot.label}</div>
                          <div className="text-[9px] opacity-75 font-mono">{slot.time}</div>
                        </button>
                      ))}
                    </div>
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-slate-300 mb-1.5">Delivery Priority</label>
                    <div className="grid grid-cols-3 gap-2">
                      {['LOW', 'MEDIUM', 'HIGH'].map((p) => (
                        <button
                          key={p}
                          type="button"
                          onClick={() => setBookingForm({ ...bookingForm, priority: p })}
                          className={`py-1.5 rounded-lg text-xs font-bold transition cursor-pointer border ${
                            bookingForm.priority === p
                              ? 'bg-indigo-600 text-white border-indigo-500 shadow-md'
                              : 'bg-slate-950 text-slate-400 border-slate-800 hover:bg-slate-800'
                          }`}
                        >
                          {p}
                        </button>
                      ))}
                    </div>
                  </div>

                  <div className="pt-2 border-t border-slate-800/80 space-y-2 text-xs">
                    <label className="flex items-center gap-2 cursor-pointer text-slate-300">
                      <input
                        type="checkbox"
                        checked={bookingForm.is_fragile}
                        onChange={(e) => setBookingForm({ ...bookingForm, is_fragile: e.target.checked })}
                        className="rounded border-slate-700 bg-slate-950 text-indigo-600 focus:ring-0"
                      />
                      <span>Handle as Fragile Item</span>
                    </label>

                    <label className="flex items-center gap-2 cursor-pointer text-slate-300">
                      <input
                        type="checkbox"
                        checked={bookingForm.requires_cold_storage}
                        onChange={(e) => setBookingForm({ ...bookingForm, requires_cold_storage: e.target.checked })}
                        className="rounded border-slate-700 bg-slate-950 text-indigo-600 focus:ring-0"
                      />
                      <span>Requires Cold Storage (Temperature Controlled)</span>
                    </label>
                  </div>
                </div>
              </div>

              {/* Live Cost Estimation Summary Card */}
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
                <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                  <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-2">
                    <Coins className="w-4 h-4 text-emerald-400" />
                    <span>Instant Price Breakdown</span>
                  </h3>
                  <span className="text-[10px] text-emerald-400 font-bold uppercase">Zero Hidden Fees</span>
                </div>

                <div className="space-y-2 text-xs">
                  <div className="flex items-center justify-between text-slate-400">
                    <span>Direct Route Distance:</span>
                    <span className="font-mono text-white font-semibold">{calculatedDistanceKm} km</span>
                  </div>
                  <div className="flex items-center justify-between text-slate-400">
                    <span>Base Logistics Staging Fee:</span>
                    <span className="font-mono text-slate-300">₹50.00</span>
                  </div>
                  <div className="flex items-center justify-between text-slate-400">
                    <span>Distance Surcharge (₹12/km):</span>
                    <span className="font-mono text-slate-300">₹{(calculatedDistanceKm * 12).toFixed(2)}</span>
                  </div>
                  <div className="flex items-center justify-between text-slate-400">
                    <span>Payload Weight Charge (₹5/kg):</span>
                    <span className="font-mono text-slate-300">₹{(Number(bookingForm.weight_kg || 0) * 5).toFixed(2)}</span>
                  </div>

                  <div className="p-3.5 bg-gradient-to-r from-emerald-950/40 to-slate-950 border border-emerald-500/30 rounded-xl mt-3 flex items-center justify-between">
                    <div>
                      <div className="text-[10px] text-emerald-400 font-bold uppercase tracking-widest">
                        Total Guaranteed Estimate
                      </div>
                      <div className="text-2xl font-black text-white font-mono mt-0.5">
                        ₹{estimatedBookingCost}.00
                      </div>
                    </div>
                    <Truck className="w-8 h-8 text-emerald-400 opacity-80" />
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={bookingLoading}
                  className="w-full py-3 rounded-xl bg-gradient-to-r from-emerald-600 to-indigo-600 hover:from-emerald-500 hover:to-indigo-500 text-white font-bold text-xs uppercase tracking-wider shadow-lg shadow-emerald-600/20 transition flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
                >
                  <Send className={`w-4 h-4 ${bookingLoading ? 'animate-spin' : ''}`} />
                  <span>{bookingLoading ? 'Registering Delivery...' : 'Book Delivery Ride Now'}</span>
                </button>
              </div>
            </div>
          </div>
        </form>
      )}

      {/* Tab 3: Cost Estimator */}
      {activeTab === 'calculator' && (
        <CustomerCostCalculator />
      )}
    </div>
  );
}
