import React, { useState, useEffect, useRef } from 'react';
import {
  Radio,
  Navigation,
  Compass,
  Gauge,
  CheckCircle,
  AlertOctagon,
  Clock,
  ShieldCheck,
  StopCircle,
  PlayCircle,
} from 'lucide-react';
import { apiClient } from '../api/client';

export const DriverLocationBroadcaster = ({
  activeDeliveryId,
  driverName = 'Fleet Driver',
  onLocationUpdate,
}) => {
  const [isBroadcasting, setIsBroadcasting] = useState(false);
  const [currentCoords, setCurrentCoords] = useState(null);
  const [accuracy, setAccuracy] = useState(null);
  const [speedKmph, setSpeedKmph] = useState(0);
  const [heading, setHeading] = useState(null);
  const [pingCount, setPingCount] = useState(0);
  const [lastPingTime, setLastPingTime] = useState(null);
  const [errorStatus, setErrorStatus] = useState(null); // 'PERMISSION_DENIED', 'UNSUPPORTED', etc.

  const watchIdRef = useRef(null);

  // Send ping to backend
  const sendPingToBackend = async (lat, lon, speed, acc, head) => {
    try {
      if (activeDeliveryId) {
        await apiClient.post(`/api/v1/tracking/${activeDeliveryId}/ping`, {
          latitude: lat,
          longitude: lon,
          speed_kmph: speed || 0,
          accuracy_meters: acc,
          heading_degrees: head,
        });
      } else {
        await apiClient.post('/api/v1/drivers/location', {
          latitude: lat,
          longitude: lon,
        });
      }

      setPingCount((prev) => prev + 1);
      setLastPingTime(new Date());
      setErrorStatus(null);

      if (onLocationUpdate) {
        onLocationUpdate({ latitude: lat, longitude: lon, speed, accuracy: acc, heading: head });
      }
    } catch (err) {
      console.warn('Failed transmitting driver GPS telemetry:', err);
    }
  };

  const startBroadcasting = () => {
    if (!('geolocation' in navigator)) {
      setErrorStatus('UNSUPPORTED');
      return;
    }

    setErrorStatus(null);
    setIsBroadcasting(true);

    const id = navigator.geolocation.watchPosition(
      (position) => {
        const { latitude, longitude, speed, accuracy: acc, heading: head } = position.coords;
        const speedVal = speed !== null && speed >= 0 ? Math.round(speed * 3.6) : 0; // m/s to km/h

        setCurrentCoords({ lat: latitude, lon: longitude });
        setSpeedKmph(speedVal);
        setAccuracy(acc ? Math.round(acc) : null);
        setHeading(head ? Math.round(head) : null);

        sendPingToBackend(latitude, longitude, speedVal, acc, head);
      },
      (error) => {
        if (error.code === error.PERMISSION_DENIED) {
          setErrorStatus('PERMISSION_DENIED');
        } else if (error.code === error.POSITION_UNAVAILABLE) {
          setErrorStatus('POSITION_UNAVAILABLE');
        } else if (error.code === error.TIMEOUT) {
          setErrorStatus('TIMEOUT');
        }
        setIsBroadcasting(false);
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 2000,
      }
    );

    watchIdRef.current = id;
  };

  const stopBroadcasting = () => {
    if (watchIdRef.current !== null) {
      navigator.geolocation.clearWatch(watchIdRef.current);
      watchIdRef.current = null;
    }
    setIsBroadcasting(false);
  };

  useEffect(() => {
    return () => {
      if (watchIdRef.current !== null) {
        navigator.geolocation.clearWatch(watchIdRef.current);
      }
    };
  }, []);

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-6">
      {/* Header & Toggle Button */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div className="flex items-center space-x-3">
          <div
            className={`w-12 h-12 rounded-xl flex items-center justify-center ${
              isBroadcasting ? 'bg-emerald-500/20 text-emerald-400' : 'bg-slate-800 text-slate-400'
            }`}
          >
            <Radio className={`w-6 h-6 ${isBroadcasting ? 'animate-pulse' : ''}`} />
          </div>
          <div>
            <h3 className="text-lg font-bold text-white flex items-center gap-2">
              <span>Driver Real-Time Telemetry</span>
              {isBroadcasting && (
                <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 uppercase tracking-wider animate-pulse">
                  Broadcasting Live
                </span>
              )}
            </h3>
            <p className="text-xs text-slate-400">
              Streams precise W3C browser coordinates to customer map & warehouse dispatch
            </p>
          </div>
        </div>

        {/* Action Toggle */}
        <div>
          {isBroadcasting ? (
            <button
              onClick={stopBroadcasting}
              className="px-5 py-2.5 rounded-xl bg-rose-600 hover:bg-rose-700 text-white font-semibold text-sm shadow-lg shadow-rose-600/20 flex items-center space-x-2 transition cursor-pointer"
            >
              <StopCircle className="w-4 h-4" />
              <span>Stop Broadcasting</span>
            </button>
          ) : (
            <button
              onClick={startBroadcasting}
              className="px-5 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-sm shadow-lg shadow-emerald-600/20 flex items-center space-x-2 transition cursor-pointer"
            >
              <PlayCircle className="w-4 h-4" />
              <span>Start Live GPS Stream</span>
            </button>
          )}
        </div>
      </div>

      {/* Permission / Unsupported Error Alerts */}
      {errorStatus && (
        <div className="p-4 rounded-xl bg-rose-950/60 border border-rose-500/50 text-rose-200 text-xs flex items-start space-x-3">
          <AlertOctagon className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
          <div>
            <div className="font-bold text-sm">
              {errorStatus === 'PERMISSION_DENIED'
                ? 'Geolocation Permission Denied'
                : errorStatus === 'UNSUPPORTED'
                ? 'Browser Does Not Support Geolocation'
                : 'GPS Location Timeout'}
            </div>
            <div className="mt-1 text-slate-300">
              {errorStatus === 'PERMISSION_DENIED'
                ? 'Please allow location access in your browser address bar permissions to broadcast your route.'
                : 'Your browser cannot read device coordinates. Please use Chrome, Edge, or Firefox on mobile/desktop.'}
            </div>
          </div>
        </div>
      )}

      {/* Live Telemetry Sensor Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {/* Speed */}
        <div className="bg-slate-950/70 border border-slate-800 rounded-xl p-4">
          <div className="flex items-center space-x-2 text-slate-400 text-xs font-semibold uppercase">
            <Gauge className="w-4 h-4 text-indigo-400" />
            <span>Speed</span>
          </div>
          <div className="mt-2 text-2xl font-black text-white">
            {speedKmph} <span className="text-xs font-normal text-slate-400">km/h</span>
          </div>
        </div>

        {/* GPS Accuracy */}
        <div className="bg-slate-950/70 border border-slate-800 rounded-xl p-4">
          <div className="flex items-center space-x-2 text-slate-400 text-xs font-semibold uppercase">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            <span>GPS Accuracy</span>
          </div>
          <div className="mt-2 text-2xl font-black text-white">
            {accuracy !== null ? `±${accuracy}` : '--'}{' '}
            <span className="text-xs font-normal text-slate-400">meters</span>
          </div>
        </div>

        {/* Heading */}
        <div className="bg-slate-950/70 border border-slate-800 rounded-xl p-4">
          <div className="flex items-center space-x-2 text-slate-400 text-xs font-semibold uppercase">
            <Compass className="w-4 h-4 text-amber-400" />
            <span>Heading</span>
          </div>
          <div className="mt-2 text-2xl font-black text-white">
            {heading !== null ? `${heading}°` : '--'}
          </div>
        </div>

        {/* Transmitted Pings */}
        <div className="bg-slate-950/70 border border-slate-800 rounded-xl p-4">
          <div className="flex items-center space-x-2 text-slate-400 text-xs font-semibold uppercase">
            <Clock className="w-4 h-4 text-purple-400" />
            <span>Packets Sent</span>
          </div>
          <div className="mt-2 text-2xl font-black text-white">{pingCount}</div>
        </div>
      </div>

      {/* Lat/Lon Coordinates Bar */}
      {currentCoords && (
        <div className="bg-slate-950/90 border border-slate-800 rounded-xl px-4 py-3 flex flex-wrap items-center justify-between text-xs font-mono text-slate-300">
          <div className="flex items-center space-x-2">
            <Navigation className="w-4 h-4 text-indigo-400" />
            <span>
              LAT: <b className="text-white">{currentCoords.lat.toFixed(6)}</b>, LON:{' '}
              <b className="text-white">{currentCoords.lon.toFixed(6)}</b>
            </span>
          </div>
          {lastPingTime && (
            <div className="text-slate-500">
              Last Broadcast: {lastPingTime.toLocaleTimeString()}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
