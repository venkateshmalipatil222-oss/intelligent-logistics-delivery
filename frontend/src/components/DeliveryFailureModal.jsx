import React, { useState } from 'react';
import {
  AlertOctagon,
  X,
  FileText,
  Camera,
  MapPin,
  CheckCircle,
  AlertTriangle,
} from 'lucide-react';
import { reportDeliveryFailure } from '../api/client';

export const DeliveryFailureModal = ({
  isOpen,
  onClose,
  delivery,
  onSuccess,
}) => {
  const [reason, setReason] = useState('RECIPIENT_UNAVAILABLE');
  const [notes, setNotes] = useState('');
  const [photoUrl, setPhotoUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  if (!isOpen || !delivery) return null;

  const failureReasons = [
    { value: 'RECIPIENT_UNAVAILABLE', label: 'Recipient Unavailable / Not Answering' },
    { value: 'INCORRECT_ADDRESS', label: 'Incorrect / Incomplete Destination Address' },
    { value: 'CUSTOMER_REJECTED', label: 'Customer Rejected / Cancelled at Doorstep' },
    { value: 'ACCESS_RESTRICTED', label: 'Access Restricted / Gated Facility Closed' },
    { value: 'DAMAGED_PACKAGE', label: 'Damaged Package Discovered Upon Handover' },
    { value: 'WEATHER_OR_FORCE_MAJEURE', label: 'Severe Weather / Road Closure' },
    { value: 'OTHER', label: 'Other Operational Exception' },
  ];

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (notes.trim().length < 5) {
      setError('Please provide at least 5 characters explaining the delivery issue.');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const updated = await reportDeliveryFailure(delivery.id, {
        reason,
        notes: notes.trim(),
        photo_url: photoUrl.trim() || undefined,
      });
      if (onSuccess) {
        onSuccess(updated);
      }
      onClose();
    } catch (err) {
      setError(err.normalizedMessage || 'Failed to submit delivery exception report');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-in fade-in duration-150">
      <div className="w-full max-w-lg bg-slate-900 border border-slate-700 rounded-2xl shadow-2xl overflow-hidden space-y-5">
        {/* Modal Header */}
        <div className="px-6 py-4 bg-rose-950/40 border-b border-rose-500/30 flex items-center justify-between">
          <div className="flex items-center space-x-2.5">
            <div className="p-2 rounded-xl bg-rose-500/20 text-rose-400">
              <AlertOctagon className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                Report Delivery Exception / Failure
              </h3>
              <p className="text-[11px] text-rose-300">
                Delivery #{delivery.delivery_number} &bull; Order #{delivery.order_id}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Form */}
        <form onSubmit={handleSubmit} className="px-6 space-y-4">
          {error && (
            <div className="p-3.5 rounded-xl bg-rose-950/70 border border-rose-500/40 text-rose-200 text-xs flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Reason Selector */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
              Reason for Non-Delivery <span className="text-rose-400">*</span>
            </label>
            <select
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              className="w-full px-3.5 py-2.5 bg-slate-950 border border-slate-700 rounded-xl text-white text-xs font-medium focus:border-rose-500 focus:outline-none"
            >
              {failureReasons.map((r) => (
                <option key={r.value} value={r.value}>
                  {r.label}
                </option>
              ))}
            </select>
          </div>

          {/* Driver Explanatory Notes */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center justify-between">
              <span>Detailed Driver Remarks <span className="text-rose-400">*</span></span>
              <span className="text-[10px] text-slate-500">{notes.length}/500</span>
            </label>
            <textarea
              rows={3}
              maxLength={500}
              placeholder="e.g. Arrived at gate 4, recipient phone went unanswered 3 times, security stated recipient out of town..."
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              className="w-full px-3.5 py-2.5 bg-slate-950 border border-slate-700 rounded-xl text-white text-xs placeholder-slate-500 focus:border-rose-500 focus:outline-none resize-none"
            />
          </div>

          {/* Proof of Exception Photo URL */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
              <Camera className="w-3.5 h-3.5 text-slate-400" />
              <span>Proof Photo URL (Optional)</span>
            </label>
            <input
              type="url"
              placeholder="https://cdn.ildo.com/proof/locked_gate.jpg"
              value={photoUrl}
              onChange={(e) => setPhotoUrl(e.target.value)}
              className="w-full px-3.5 py-2 bg-slate-950 border border-slate-700 rounded-xl text-white text-xs placeholder-slate-500 focus:border-indigo-500 focus:outline-none"
            />
          </div>

          <p className="text-[11px] text-slate-500">
            Note: Submitting a failure report transitions this delivery to <b>FAILED</b>, frees the vehicle, and automatically dispatches a critical alert to the customer and hub manager.
          </p>

          {/* Actions */}
          <div className="pt-2 pb-5 flex items-center justify-end gap-3 border-t border-slate-800">
            <button
              type="button"
              onClick={onClose}
              disabled={loading}
              className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading || notes.trim().length < 5}
              className="px-5 py-2 rounded-xl bg-rose-600 hover:bg-rose-500 text-white text-xs font-semibold shadow-lg shadow-rose-600/20 transition disabled:opacity-50"
            >
              {loading ? 'Submitting...' : 'Submit Failure Report'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
