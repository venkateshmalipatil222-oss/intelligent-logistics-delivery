import React, { useState, useEffect } from 'react';
import {
  Server,
  Database,
  Activity,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  Clock,
  Cpu,
  Layers,
  ArrowRight,
  Shield,
  Zap
} from 'lucide-react';
import { getSystemHealth, pingBackend } from '../api/client';

export default function HealthDashboard({ health, setHealth }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [pingData, setPingData] = useState(null);
  const [lastCheck, setLastCheck] = useState(new Date().toLocaleTimeString());

  const fetchHealth = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getSystemHealth();
      setHealth(data);
      const ping = await pingBackend();
      setPingData(ping);
      setLastCheck(new Date().toLocaleTimeString());
    } catch (err) {
      setError(err.normalizedMessage || 'Backend server is currently offline or unreachable.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHealth();
    // Auto-refresh every 30 seconds
    const interval = setInterval(fetchHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  const db = health?.dependencies?.database || {};
  const isHealthy = health?.status === 'healthy';

  const roadmapPhases = [
    { id: 0, name: 'Phase 0: Audit & Architecture', status: 'completed', desc: 'Environment inspection, runtime checks, architectural blueprint.' },
    { id: 1, name: 'Phase 1: Stable Foundation', status: 'active', desc: 'FastAPI startup, MySQL connection pool, health endpoints, React layout.' },
    { id: 2, name: 'Phase 2: Authentication & RBAC', status: 'pending', desc: 'JWT token issuance, bcrypt hashing, Admin, Warehouse, Driver, Customer roles.' },
    { id: 3, name: 'Phase 3: Core Logistics Pipeline', status: 'pending', desc: 'Order lifecycle, warehouse staging, drivers, vehicles, dispatch state machine.' },
    { id: 4, name: 'Phase 4: Assignment & Routing', status: 'pending', desc: 'Multi-factor driver scoring, Dijkstra graph routing, nearest-neighbor heuristics.' },
    { id: 5, name: 'Phase 5: Real-time Geolocation', status: 'pending', desc: 'Browser GPS updates, WebSocket streaming, live Leaflet map, ETA engine.' },
    { id: 6, name: 'Phase 6: Proof of Delivery', status: 'pending', desc: 'Time-limited OTP verification, driver confirmation, event notifications.' },
    { id: 7, name: 'Phase 7: Multi-Role Dashboards', status: 'pending', desc: 'Admin analytics, warehouse dispatch queues, driver mobile view, customer portal.' },
    { id: 8, name: 'Phase 8: Testing & Hardening', status: 'pending', desc: 'Automated Pytest suite, edge-case validation, migration regression tests.' },
    { id: 9, name: 'Phase 9: Final Delivery & Docs', status: 'pending', desc: 'Seed data script, Docker Compose, interview viva guide, GitHub release.' },
  ];

  return (
    <div className="max-w-7xl mx-auto px-6 py-8 space-y-8">
      {/* Hero / Header */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 pb-6 border-b border-slate-800">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
            System & Infrastructure Health Monitor
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Real-time status of backend micro-services, database pools, and algorithmic engine readiness.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <span className="text-xs text-slate-400">Last checked: <span className="font-mono text-slate-300">{lastCheck}</span></span>
          <button
            onClick={fetchHealth}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-md shadow-indigo-600/30 transition-all disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>{loading ? 'Verifying...' : 'Refresh Telemetry'}</span>
          </button>
        </div>
      </div>

      {/* Error alert if backend unreachable */}
      {error && (
        <div className="p-4 rounded-xl bg-red-950/60 border border-red-800/80 text-red-200 flex items-start gap-3 shadow-lg">
          <AlertTriangle className="w-5 h-5 text-red-400 shrink-0 mt-0.5" />
          <div>
            <h4 className="font-semibold text-sm text-red-300">Connection Telemetry Error</h4>
            <p className="text-xs text-red-300/80 mt-0.5">{error}</p>
            <p className="text-xs text-red-400 mt-2 font-mono">Ensure backend server is running on http://127.0.0.1:8000</p>
          </div>
        </div>
      )}

      {/* Primary KPI Status Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        {/* API Server Card */}
        <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-sm hover:border-slate-700 transition-all">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">API Gateway</span>
            <div className={`p-2 rounded-lg ${isHealthy ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'}`}>
              <Server className="w-4 h-4" />
            </div>
          </div>
          <div className="text-xl font-bold text-white mb-1">
            {isHealthy ? 'Operational' : 'Unhealthy'}
          </div>
          <div className="flex items-center justify-between text-xs text-slate-400 pt-2 border-t border-slate-800/80">
            <span>Uptime</span>
            <span className="font-mono text-slate-200">{health?.uptime_seconds ? `${health.uptime_seconds}s` : 'N/A'}</span>
          </div>
        </div>

        {/* Database Card */}
        <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-sm hover:border-slate-700 transition-all">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">MySQL Database</span>
            <div className={`p-2 rounded-lg ${db?.status === 'connected' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'}`}>
              <Database className="w-4 h-4" />
            </div>
          </div>
          <div className="text-xl font-bold text-white mb-1">
            {db?.status === 'connected' ? 'Connected' : 'Disconnected'}
          </div>
          <div className="flex items-center justify-between text-xs text-slate-400 pt-2 border-t border-slate-800/80">
            <span>Query Latency</span>
            <span className="font-mono text-emerald-400 font-semibold">{db?.latency_ms ? `${db.latency_ms} ms` : 'N/A'}</span>
          </div>
        </div>

        {/* Environment Card */}
        <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-sm hover:border-slate-700 transition-all">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Environment</span>
            <div className="p-2 rounded-lg bg-indigo-500/10 text-indigo-400">
              <Cpu className="w-4 h-4" />
            </div>
          </div>
          <div className="text-xl font-bold text-white mb-1 capitalize">
            {health?.environment || 'Development'}
          </div>
          <div className="flex items-center justify-between text-xs text-slate-400 pt-2 border-t border-slate-800/80">
            <span>Python Runtime</span>
            <span className="font-mono text-slate-200">{health?.system?.python_version || '3.13.0'}</span>
          </div>
        </div>

        {/* Liveness Ping Card */}
        <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-sm hover:border-slate-700 transition-all">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Heartbeat Ping</span>
            <div className="p-2 rounded-lg bg-blue-500/10 text-blue-400">
              <Zap className="w-4 h-4" />
            </div>
          </div>
          <div className="text-xl font-bold text-white mb-1">
            {pingData?.ping === 'pong' ? '200 OK (Pong)' : 'Awaiting Ping'}
          </div>
          <div className="flex items-center justify-between text-xs text-slate-400 pt-2 border-t border-slate-800/80">
            <span>PID</span>
            <span className="font-mono text-slate-200">{health?.system?.process_id || 'Active'}</span>
          </div>
        </div>
      </div>

      {/* Technical Telemetry Details Table */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-6 shadow-sm">
        <h3 className="text-base font-bold text-white mb-4 flex items-center gap-2">
          <Activity className="w-4 h-4 text-indigo-400" />
          <span>Active Component Telemetry</span>
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono">
          <div className="p-3.5 rounded-lg bg-slate-950/80 border border-slate-800/80 space-y-1.5">
            <div className="text-slate-400 font-sans font-medium">Database Target:</div>
            <div className="text-indigo-300 font-bold">{db?.dialect ? `${db.dialect.toUpperCase()} (${db.database})` : 'N/A'}</div>
            <div className="text-[11px] text-slate-500">Connection pooling: pool_pre_ping=True, pool_recycle=3600</div>
          </div>
          <div className="p-3.5 rounded-lg bg-slate-950/80 border border-slate-800/80 space-y-1.5">
            <div className="text-slate-400 font-sans font-medium">Operating System & Host:</div>
            <div className="text-slate-300 truncate">{health?.system?.platform || 'Windows 11 AMD64'}</div>
            <div className="text-[11px] text-slate-500">FastAPI 0.141.1 with Uvicorn ASGI Server</div>
          </div>
        </div>
      </div>

      {/* Phase Roadmap Progression */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-6 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            <Layers className="w-4 h-4 text-indigo-400" />
            <span>Implementation Phase Roadmap</span>
          </h3>
          <span className="text-xs px-2.5 py-1 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 font-semibold">
            Phase 1 Active
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {roadmapPhases.map((phase) => (
            <div
              key={phase.id}
              className={`p-3.5 rounded-lg border transition-all flex items-start gap-3 ${
                phase.status === 'completed'
                  ? 'bg-slate-950/40 border-emerald-500/20 text-slate-300'
                  : phase.status === 'active'
                  ? 'bg-indigo-950/20 border-indigo-500/40 text-slate-100 shadow-md shadow-indigo-500/5'
                  : 'bg-slate-950/20 border-slate-800/60 text-slate-500'
              }`}
            >
              <div className="mt-0.5">
                {phase.status === 'completed' ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                ) : phase.status === 'active' ? (
                  <div className="w-4 h-4 rounded-full border-2 border-indigo-400 border-t-transparent animate-spin" />
                ) : (
                  <div className="w-4 h-4 rounded-full border border-slate-700 flex items-center justify-center text-[9px] font-bold">
                    {phase.id}
                  </div>
                )}
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h4 className="font-semibold text-xs text-white">{phase.name}</h4>
                  {phase.status === 'active' && (
                    <span className="text-[10px] px-1.5 py-0.2 rounded bg-indigo-500/20 text-indigo-300 font-bold uppercase">
                      Current
                    </span>
                  )}
                </div>
                <p className="text-[11px] text-slate-400 mt-0.5">{phase.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
