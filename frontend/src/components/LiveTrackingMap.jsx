import React, { useEffect, useRef } from 'react';
import L from 'leaflet';
import {
  Navigation,
  Clock,
  AlertTriangle,
  CheckCircle2,
  Radio,
  RefreshCw,
  Maximize2,
  ShieldAlert,
  Zap,
} from 'lucide-react';

export const LiveTrackingMap = ({
  trackingData,
  connectionStatus = 'CONNECTED',
  onRefresh,
}) => {
  const mapContainerRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const markersRef = useRef({ warehouse: null, driver: null, destination: null });
  const polylineRef = useRef(null);

  // Initialize Map
  useEffect(() => {
    if (!mapContainerRef.current || mapInstanceRef.current) return;

    const initialLat = trackingData?.current_driver_location?.latitude || 12.9716;
    const initialLon = trackingData?.current_driver_location?.longitude || 77.5946;

    const map = L.map(mapContainerRef.current, {
      center: [initialLat, initialLon],
      zoom: 13,
      zoomControl: false,
    });

    // Dark sleek CartoDB tile layer for modern logistics aesthetics
    L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
      attribution: '&copy; OpenStreetMap contributors &copy; CARTO',
      subdomains: 'abcd',
      maxZoom: 19,
    }).addTo(map);

    L.control.zoom({ position: 'bottomright' }).addTo(map);

    mapInstanceRef.current = map;

    return () => {
      map.remove();
      mapInstanceRef.current = null;
    };
  }, []);

  // Update Markers and Polyline when trackingData changes
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map || !trackingData) return;

    const { origin_warehouse, destination, current_driver_location } = trackingData;

    // Helper for custom HTML markers
    const createCustomIcon = (bgColor, innerContent, isPulse = false) => {
      return L.divIcon({
        className: 'custom-leaflet-marker',
        html: `
          <div class="relative flex items-center justify-center">
            ${isPulse ? '<span class="absolute inline-flex h-12 w-12 rounded-full bg-emerald-400 opacity-35 animate-ping"></span>' : ''}
            <div class="relative w-10 h-10 rounded-full ${bgColor} text-white shadow-xl flex items-center justify-center font-bold text-xs border-2 border-white">
              ${innerContent}
            </div>
          </div>
        `,
        iconSize: [40, 40],
        iconAnchor: [20, 20],
      });
    };

    // 1. Warehouse Marker
    if (origin_warehouse?.latitude && origin_warehouse?.longitude) {
      const whPos = [origin_warehouse.latitude, origin_warehouse.longitude];
      if (!markersRef.current.warehouse) {
        markersRef.current.warehouse = L.marker(whPos, {
          icon: createCustomIcon('bg-indigo-600', '🏭'),
        })
          .addTo(map)
          .bindPopup(`<b>${origin_warehouse.name}</b><br>Origin Fulfillment Hub`);
      } else {
        markersRef.current.warehouse.setLatLng(whPos);
      }
    }

    // 2. Driver Marker (pulsing live location)
    if (current_driver_location?.latitude && current_driver_location?.longitude) {
      const drvPos = [current_driver_location.latitude, current_driver_location.longitude];
      if (!markersRef.current.driver) {
        markersRef.current.driver = L.marker(drvPos, {
          icon: createCustomIcon('bg-emerald-600', '🚚', true),
        })
          .addTo(map)
          .bindPopup(
            `<b>${trackingData.driver_name}</b><br>Vehicle: ${trackingData.vehicle_registration || 'Fleet Vehicle'}<br>Status: ${trackingData.status}`
          );
      } else {
        markersRef.current.driver.setLatLng(drvPos);
      }
    }

    // 3. Destination Marker
    if (destination?.latitude && destination?.longitude) {
      const destPos = [destination.latitude, destination.longitude];
      if (!markersRef.current.destination) {
        markersRef.current.destination = L.marker(destPos, {
          icon: createCustomIcon('bg-rose-600', '📍'),
        })
          .addTo(map)
          .bindPopup(`<b>${destination.name}</b><br>Customer Drop-off Location`);
      } else {
        markersRef.current.destination.setLatLng(destPos);
      }
    }

    // 4. Update Polyline connecting Origin -> Driver -> Destination
    const points = [];
    if (origin_warehouse?.latitude && origin_warehouse?.longitude) {
      points.push([origin_warehouse.latitude, origin_warehouse.longitude]);
    }
    if (current_driver_location?.latitude && current_driver_location?.longitude) {
      points.push([current_driver_location.latitude, current_driver_location.longitude]);
    }
    if (destination?.latitude && destination?.longitude) {
      points.push([destination.latitude, destination.longitude]);
    }

    if (points.length >= 2) {
      if (polylineRef.current) {
        polylineRef.current.setLatLngs(points);
      } else {
        polylineRef.current = L.polyline(points, {
          color: '#4f46e5',
          weight: 4,
          opacity: 0.85,
          dashArray: '8, 8',
        }).addTo(map);
      }
    }
  }, [trackingData]);

  // Fit bounds helper
  const handleFitBounds = () => {
    const map = mapInstanceRef.current;
    if (!map || !trackingData) return;

    const bounds = [];
    if (trackingData.origin_warehouse?.latitude) {
      bounds.push([trackingData.origin_warehouse.latitude, trackingData.origin_warehouse.longitude]);
    }
    if (trackingData.current_driver_location?.latitude) {
      bounds.push([trackingData.current_driver_location.latitude, trackingData.current_driver_location.longitude]);
    }
    if (trackingData.destination?.latitude) {
      bounds.push([trackingData.destination.latitude, trackingData.destination.longitude]);
    }

    if (bounds.length > 0) {
      map.fitBounds(bounds, { padding: [60, 60] });
    }
  };

  // Helper formatting arrival time
  const formatTime = (isoString) => {
    if (!isoString) return '--:--';
    try {
      const d = new Date(isoString);
      return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } catch {
      return '--:--';
    }
  };

  const getDelayBadgeClass = (riskLevel) => {
    switch (riskLevel) {
      case 'HIGH':
        return 'bg-rose-500/20 text-rose-300 border-rose-500/40';
      case 'MEDIUM':
        return 'bg-amber-500/20 text-amber-300 border-amber-500/40';
      case 'LOW':
        return 'bg-yellow-500/20 text-yellow-300 border-yellow-500/40';
      default:
        return 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40';
    }
  };

  return (
    <div className="relative w-full h-[520px] rounded-2xl overflow-hidden shadow-2xl border border-slate-800 bg-slate-900">
      {/* Top Floating Telemetry & ETA HUD Overlay */}
      <div className="absolute top-4 left-4 right-4 z-20 flex flex-wrap items-center justify-between gap-3 pointer-events-none">
        {/* ETA & Distance Card */}
        <div className="pointer-events-auto bg-slate-900/90 backdrop-blur-md px-4 py-2.5 rounded-xl border border-slate-700/80 shadow-lg flex items-center space-x-4">
          <div className="p-2 rounded-lg bg-indigo-500/20 text-indigo-400">
            <Clock className="w-5 h-5" />
          </div>
          <div>
            <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Estimated Arrival</div>
            <div className="text-lg font-bold text-white flex items-center gap-1.5">
              <span>{formatTime(trackingData?.estimated_arrival_time)}</span>
              <span className="text-xs text-slate-400 font-normal">
                (±{trackingData?.uncertainty_buffer_minutes || 5}m)
              </span>
            </div>
          </div>
          <div className="h-8 w-px bg-slate-700 mx-1"></div>
          <div>
            <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Distance</div>
            <div className="text-lg font-bold text-white">
              {trackingData?.remaining_distance_km ? `${trackingData.remaining_distance_km} km` : 'Calculating...'}
            </div>
          </div>
        </div>

        {/* Right Status Badges */}
        <div className="pointer-events-auto flex items-center space-x-2">
          {/* Connection Pulse */}
          <div
            className={`px-3 py-1.5 rounded-lg border text-xs font-medium flex items-center space-x-1.5 backdrop-blur-md shadow-md ${
              connectionStatus === 'CONNECTED'
                ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'
                : connectionStatus === 'FALLBACK_POLLING'
                ? 'bg-amber-500/20 text-amber-300 border-amber-500/40 animate-pulse'
                : 'bg-rose-500/20 text-rose-300 border-rose-500/40'
            }`}
          >
            <Radio className="w-3.5 h-3.5 animate-pulse" />
            <span>
              {connectionStatus === 'CONNECTED'
                ? 'WebSocket Live'
                : connectionStatus === 'FALLBACK_POLLING'
                ? 'REST Polling'
                : 'Disconnected'}
            </span>
          </div>

          {/* Delay Risk Badge */}
          {trackingData?.delay_risk_level && (
            <div
              className={`px-3 py-1.5 rounded-lg border text-xs font-medium flex items-center space-x-1.5 backdrop-blur-md shadow-md ${getDelayBadgeClass(
                trackingData.delay_risk_level
              )}`}
            >
              <AlertTriangle className="w-3.5 h-3.5" />
              <span>Risk: {trackingData.delay_risk_level}</span>
            </div>
          )}

          {/* Controls: Fit Bounds & Refresh */}
          <button
            onClick={handleFitBounds}
            title="Fit Route to Screen"
            className="p-2 rounded-lg bg-slate-800/90 hover:bg-slate-700 text-slate-200 border border-slate-700 shadow-md transition"
          >
            <Maximize2 className="w-4 h-4" />
          </button>
          {onRefresh && (
            <button
              onClick={onRefresh}
              title="Refresh Telemetry"
              className="p-2 rounded-lg bg-slate-800/90 hover:bg-slate-700 text-slate-200 border border-slate-700 shadow-md transition"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>

      {/* Telemetry Staleness Alert Banner (if ping > 10 mins ago) */}
      {trackingData?.is_telemetry_stale && (
        <div className="absolute bottom-4 left-4 right-4 z-20 pointer-events-auto bg-amber-950/90 border border-amber-600/70 text-amber-200 text-xs px-4 py-2.5 rounded-xl backdrop-blur-md flex items-center justify-between shadow-xl">
          <div className="flex items-center space-x-2">
            <ShieldAlert className="w-4 h-4 text-amber-400 shrink-0" />
            <span>
              <b>Telemetry Warning:</b> Driver GPS telemetry is stale (last ping was{' '}
              {trackingData.last_ping_seconds_ago
                ? `${Math.round(trackingData.last_ping_seconds_ago / 60)} mins ago`
                : 'delayed'}
              ). Presenting last confirmed coordinates.
            </span>
          </div>
          <span className="text-[10px] uppercase bg-amber-800/50 px-2 py-0.5 rounded font-mono">STALE_DATA</span>
        </div>
      )}

      {/* Map DOM Element Container */}
      <div ref={mapContainerRef} className="w-full h-full" />
    </div>
  );
};
