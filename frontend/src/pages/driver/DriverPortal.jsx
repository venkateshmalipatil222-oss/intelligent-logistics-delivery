import React, { useState, useEffect } from 'react';
import {
  Navigation,
  MapPin,
  CheckCircle,
  Truck,
  Package,
  Clock,
  ShieldCheck,
  AlertCircle,
  ChevronRight,
  ArrowRight,
  KeyRound,
  Radio,
  RefreshCw,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import {
  getDriverMe,
  listDeliveries,
  transitionDeliveryStatus,
  verifyDeliveryOTP,
} from '../../api/client';
import { DriverLocationBroadcaster } from '../../components/DriverLocationBroadcaster';
import { LiveTrackingMap } from '../../components/LiveTrackingMap';
import { useLiveTracking } from '../../hooks/useLiveTracking';

export default function DriverPortal() {
  const { user } = useAuth();
  const [driverProfile, setDriverProfile] = useState(null);
  const [deliveries, setDeliveries] = useState([]);
  const [selectedDelivery, setSelectedDelivery] = useState(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [otpCode, setOtpCode] = useState('');
  const [statusMessage, setStatusMessage] = useState(null);
  const [errorMessage, setErrorMessage] = useState(null);

  // Live tracking hook for selected delivery
  const { trackingData, connectionStatus, refresh: refreshTracking } = useLiveTracking(
    selectedDelivery?.id
  );

  const fetchData = async () => {
    setLoading(true);
    setErrorMessage(null);
    try {
      const [driverRes, deliveriesRes] = await Promise.allSettled([
        getDriverMe(),
        listDeliveries(),
      ]);

      if (driverRes.status === 'fulfilled') {
        setDriverProfile(driverRes.value);
      }
      if (deliveriesRes.status === 'fulfilled') {
        const delList = deliveriesRes.value || [];
        setDeliveries(delList);
        if (delList.length > 0 && !selectedDelivery) {
          // Select first active (non-terminal) delivery or first delivery
          const active = delList.find(
            (d) => !['DELIVERED', 'CANCELLED', 'RETURNED'].includes(d.status)
          );
          setSelectedDelivery(active || delList[0]);
        }
      }
    } catch (err) {
      setErrorMessage(err.normalizedMessage || 'Failed to load driver dashboard data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  // Handle status transitions
  const handleTransition = async (nextStatus) => {
    if (!selectedDelivery) return;
    setActionLoading(true);
    setStatusMessage(null);
    setErrorMessage(null);
    try {
      const updated = await transitionDeliveryStatus(selectedDelivery.id, {
        to_status: nextStatus,
        reason: `Driver updated status to ${nextStatus}`,
        notes: `Operational state updated by driver ${user.full_name}`,
      });
      setStatusMessage(`Delivery status updated to ${nextStatus}`);
      setSelectedDelivery(updated);
      fetchData();
    } catch (err) {
      setErrorMessage(err.normalizedMessage || `Failed to transition status to ${nextStatus}`);
    } finally {
      setActionLoading(false);
    }
  };

  // Handle OTP verification
  const handleVerifyOTP = async (e) => {
    e.preventDefault();
    if (!selectedDelivery || !otpCode) return;
    setActionLoading(true);
    setStatusMessage(null);
    setErrorMessage(null);
    try {
      const result = await verifyDeliveryOTP(selectedDelivery.id, {
        otp_code: otpCode.trim(),
        notes: 'Handed over package directly to verified recipient',
      });
      setStatusMessage(`Success! Delivery ${result.delivery_number} verified and completed.`);
      setSelectedDelivery(result);
      setOtpCode('');
      fetchData();
    } catch (err) {
      setErrorMessage(err.normalizedMessage || 'Invalid OTP code. Please verify with customer.');
    } finally {
      setActionLoading(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-6 py-8 space-y-6">
      {/* Header Profile Bar */}
      <div className="flex flex-wrap items-center justify-between gap-4 pb-6 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-amber-500/10 text-amber-400 border border-amber-500/30 uppercase tracking-wider">
              Driver Mobile Cockpit
            </span>
            {driverProfile?.vehicle_registration && (
              <span className="px-2 py-0.5 rounded-full text-[10px] font-mono bg-slate-800 text-slate-300 border border-slate-700">
                {driverProfile.vehicle_registration}
              </span>
            )}
          </div>
          <h1 className="text-2xl font-extrabold text-white mt-1">Active Route & Navigation Console</h1>
          <p className="text-xs text-slate-400">
            Driver: <span className="text-slate-200 font-semibold">{user.full_name}</span> &bull;{' '}
            License: <span className="text-slate-200 font-mono">{driverProfile?.license_number || 'DL-PENDING'}</span> &bull;{' '}
            Rating: <span className="text-amber-400 font-bold">{driverProfile?.rating || '5.0'} ★</span>
          </p>
        </div>

        <button
          onClick={fetchData}
          className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold border border-slate-700 flex items-center gap-2 transition"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh Fleet Queue</span>
        </button>
      </div>

      {/* Notifications */}
      {statusMessage && (
        <div className="p-4 rounded-xl bg-emerald-950/60 border border-emerald-500/40 text-emerald-200 text-xs flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <CheckCircle className="w-4 h-4 text-emerald-400 shrink-0" />
            <span>{statusMessage}</span>
          </div>
          <button onClick={() => setStatusMessage(null)} className="text-emerald-400 hover:text-white font-bold ml-4">
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

      {/* Real-time Telemetry Broadcaster Component */}
      <DriverLocationBroadcaster
        activeDeliveryId={selectedDelivery?.id}
        driverName={user.full_name}
        onLocationUpdate={() => {
          // Trigger light refresh of map telemetry when ping successfully posts
          refreshTracking();
        }}
      />

      {/* Deliveries Queue & Selected Delivery Console */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Assigned Delivery List */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h2 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <Truck className="w-4 h-4 text-amber-400" />
              <span>Assigned Deliveries ({deliveries.length})</span>
            </h2>
          </div>

          {deliveries.length === 0 ? (
            <div className="text-center py-8 text-slate-500 text-xs">
              <Package className="w-8 h-8 mx-auto mb-2 opacity-40 text-slate-400" />
              No active deliveries currently assigned to your route.
            </div>
          ) : (
            <div className="space-y-2.5 max-h-[460px] overflow-y-auto pr-1">
              {deliveries.map((del) => {
                const isSelected = selectedDelivery?.id === del.id;
                const isTerminal = ['DELIVERED', 'CANCELLED'].includes(del.status);

                return (
                  <div
                    key={del.id}
                    onClick={() => setSelectedDelivery(del)}
                    className={`p-3.5 rounded-xl border transition cursor-pointer ${
                      isSelected
                        ? 'bg-amber-500/10 border-amber-500/40 text-white shadow-md'
                        : 'bg-slate-950/60 border-slate-800/80 hover:border-slate-700 text-slate-300'
                    }`}
                  >
                    <div className="flex items-center justify-between text-xs mb-1.5">
                      <span className="font-mono font-bold text-slate-200">{del.delivery_number}</span>
                      <span
                        className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase ${
                          del.status === 'DELIVERED'
                            ? 'bg-emerald-500/20 text-emerald-400'
                            : del.status === 'IN_TRANSIT' || del.status === 'OUT_FOR_DELIVERY'
                            ? 'bg-indigo-500/20 text-indigo-400'
                            : 'bg-amber-500/20 text-amber-400'
                        }`}
                      >
                        {del.status}
                      </span>
                    </div>

                    <div className="text-xs text-slate-400 flex items-center gap-1 truncate">
                      <MapPin className="w-3 h-3 text-rose-400 shrink-0" />
                      <span className="truncate">
                        {del.order?.destination_address || `Order #${del.order_id}`}
                      </span>
                    </div>

                    <div className="mt-2 pt-2 border-t border-slate-800/60 flex items-center justify-between text-[11px] text-slate-500">
                      <span>Order: {del.order?.order_number || `ID ${del.order_id}`}</span>
                      <span className="text-amber-400 font-medium flex items-center gap-0.5">
                        {isSelected ? 'Active Route' : 'Select'} <ChevronRight className="w-3 h-3" />
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Right 2 Columns: Active Delivery Cockpit & Map */}
        <div className="lg:col-span-2 space-y-6">
          {selectedDelivery ? (
            <>
              {/* Delivery Overview & Action Controls */}
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-5">
                <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-4">
                  <div>
                    <span className="text-[10px] font-bold text-amber-400 uppercase tracking-wider">
                      Active Navigation Target
                    </span>
                    <h3 className="text-lg font-bold text-white mt-0.5">
                      {selectedDelivery.delivery_number}
                    </h3>
                  </div>

                  {/* Operational Status Badges */}
                  <div className="flex items-center gap-2">
                    <span className="px-3 py-1 rounded-lg text-xs font-bold bg-slate-800 text-slate-300 border border-slate-700">
                      Status: <b className="text-amber-400">{selectedDelivery.status}</b>
                    </span>
                  </div>
                </div>

                {/* Destination & Order Details Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                  <div className="bg-slate-950/70 p-3.5 rounded-xl border border-slate-800/80 space-y-1.5">
                    <span className="text-[10px] font-bold uppercase text-slate-400 flex items-center gap-1">
                      <MapPin className="w-3 h-3 text-rose-400" /> Destination Drop-Off
                    </span>
                    <div className="font-semibold text-white">
                      {selectedDelivery.order?.destination_address || 'Customer Location'}
                    </div>
                    <div className="text-slate-400">
                      {selectedDelivery.order?.destination_city},{' '}
                      {selectedDelivery.order?.destination_postal_code}
                    </div>
                  </div>

                  <div className="bg-slate-950/70 p-3.5 rounded-xl border border-slate-800/80 space-y-1.5">
                    <span className="text-[10px] font-bold uppercase text-slate-400 flex items-center gap-1">
                      <Package className="w-3 h-3 text-indigo-400" /> Package Metadata
                    </span>
                    <div className="font-semibold text-white">
                      {selectedDelivery.order?.package?.category || 'Standard Goods'} &bull;{' '}
                      {selectedDelivery.order?.package?.weight_kg || '0.0'} kg
                    </div>
                    <div className="text-slate-400">
                      Tracking Ref: {selectedDelivery.order?.package?.tracking_number || 'N/A'}
                    </div>
                  </div>
                </div>

                {/* Action State Transitions */}
                <div className="border-t border-slate-800 pt-4">
                  <div className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">
                    Advance Delivery State
                  </div>

                  <div className="flex flex-wrap items-center gap-3">
                    {selectedDelivery.status === 'DISPATCHED' && (
                      <button
                        onClick={() => handleTransition('IN_TRANSIT')}
                        disabled={actionLoading}
                        className="px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs flex items-center gap-1.5 transition disabled:opacity-50"
                      >
                        <ArrowRight className="w-3.5 h-3.5" />
                        <span>Start Transit (En Route)</span>
                      </button>
                    )}

                    {selectedDelivery.status === 'IN_TRANSIT' && (
                      <button
                        onClick={() => handleTransition('OUT_FOR_DELIVERY')}
                        disabled={actionLoading}
                        className="px-4 py-2.5 rounded-xl bg-amber-600 hover:bg-amber-500 text-white font-semibold text-xs flex items-center gap-1.5 transition disabled:opacity-50"
                      >
                        <Navigation className="w-3.5 h-3.5" />
                        <span>Arrived in Neighborhood (Out for Delivery)</span>
                      </button>
                    )}

                    {['OUT_FOR_DELIVERY', 'IN_TRANSIT'].includes(selectedDelivery.status) && (
                      <form onSubmit={handleVerifyOTP} className="flex flex-wrap items-center gap-2">
                        <div className="relative">
                          <KeyRound className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                          <input
                            type="text"
                            maxLength={6}
                            placeholder="Enter 6-digit OTP"
                            value={otpCode}
                            onChange={(e) => setOtpCode(e.target.value)}
                            className="pl-8 pr-3 py-2 bg-slate-950 border border-slate-700 rounded-xl text-white text-xs font-mono tracking-widest focus:border-emerald-500 focus:outline-none w-44"
                          />
                        </div>
                        <button
                          type="submit"
                          disabled={actionLoading || otpCode.length !== 6}
                          className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-xs flex items-center gap-1.5 transition disabled:opacity-40"
                        >
                          <CheckCircle className="w-3.5 h-3.5" />
                          <span>Verify OTP & Complete</span>
                        </button>
                      </form>
                    )}

                    {selectedDelivery.status === 'DELIVERED' && (
                      <div className="px-4 py-2 rounded-xl bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 text-xs font-bold flex items-center gap-2">
                        <CheckCircle className="w-4 h-4 text-emerald-400" />
                        <span>Delivery Successfully Completed & Verified</span>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Real-Time Leaflet Route Map */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-2">
                    <Radio className="w-3.5 h-3.5 text-emerald-400 animate-pulse" />
                    <span>Live Route Visualizer & Dynamic ETA</span>
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
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-12 text-center text-slate-500 text-xs">
              Select a delivery from the queue to inspect route details and navigation.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
