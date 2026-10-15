import { useState, useEffect, useRef, useCallback } from 'react';
import { apiClient } from '../api/client';

export const useLiveTracking = (deliveryId) => {
  const [trackingData, setTrackingData] = useState(null);
  const [connectionStatus, setConnectionStatus] = useState('CONNECTING'); // 'CONNECTED' | 'FALLBACK_POLLING' | 'ERROR'
  const [error, setError] = useState(null);

  const wsRef = useRef(null);
  const pollingTimerRef = useRef(null);
  const reconnectTimerRef = useRef(null);
  const isMountedRef = useRef(true);

  // REST snapshot fetcher
  const fetchSnapshot = useCallback(async () => {
    if (!deliveryId) return;
    try {
      const response = await apiClient.get(`/api/v1/tracking/${deliveryId}/live`);
      if (isMountedRef.current) {
        setTrackingData(response.data);
        setError(null);
      }
    } catch (err) {
      if (isMountedRef.current) {
        setError(err.normalizedMessage || 'Failed to fetch tracking data');
      }
    }
  }, [deliveryId]);

  // Start REST polling fallback
  const startPolling = useCallback(() => {
    if (pollingTimerRef.current) return;
    setConnectionStatus('FALLBACK_POLLING');
    fetchSnapshot(); // Immediate initial pull
    pollingTimerRef.current = setInterval(() => {
      fetchSnapshot();
    }, 4000);
  }, [fetchSnapshot]);

  const stopPolling = useCallback(() => {
    if (pollingTimerRef.current) {
      clearInterval(pollingTimerRef.current);
      pollingTimerRef.current = null;
    }
  }, []);

  // WebSocket connection initializer
  const connectWebSocket = useCallback(() => {
    if (!deliveryId) return;

    const baseHttp = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    // If VITE_API_URL has host, replace protocol
    const wsUrl = baseHttp.replace(/^http(s)?:\/\//, `${wsProtocol}//`) + `/api/v1/tracking/ws/${deliveryId}`;

    try {
      const socket = new WebSocket(wsUrl);
      wsRef.current = socket;

      socket.onopen = () => {
        if (!isMountedRef.current) return;
        setConnectionStatus('CONNECTED');
        setError(null);
        stopPolling();
      };

      socket.onmessage = (event) => {
        if (!isMountedRef.current) return;
        try {
          const payload = JSON.parse(event.data);
          if (payload.action === 'pong') return;
          setTrackingData(payload);
        } catch {
          // Ignore parse errors on keepalive frames
        }
      };

      socket.onerror = () => {
        if (!isMountedRef.current) return;
        startPolling();
      };

      socket.onclose = () => {
        if (!isMountedRef.current) return;
        startPolling();
        // Attempt reconnect after 6 seconds
        reconnectTimerRef.current = setTimeout(() => {
          if (isMountedRef.current) {
            connectWebSocket();
          }
        }, 6000);
      };
    } catch {
      startPolling();
    }
  }, [deliveryId, startPolling, stopPolling]);

  useEffect(() => {
    isMountedRef.current = true;
    fetchSnapshot(); // First immediate REST pull so data is visible instantly
    connectWebSocket();

    // Heartbeat ping every 15s to keep WebSocket connection alive
    const pingInterval = setInterval(() => {
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ action: 'ping' }));
      }
    }, 15000);

    return () => {
      isMountedRef.current = false;
      clearInterval(pingInterval);
      stopPolling();
      if (reconnectTimerRef.current) clearTimeout(reconnectTimerRef.current);
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [deliveryId, connectWebSocket, fetchSnapshot, stopPolling]);

  return {
    trackingData,
    connectionStatus,
    error,
    refresh: fetchSnapshot,
  };
};
