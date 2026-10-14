import React from 'react';
import { Shield, GitBranch, Cpu, Database } from 'lucide-react';

export default function Footer() {
  return (
    <footer className="bg-slate-900 border-t border-slate-800 text-slate-400 text-xs py-6 mt-auto">
      <div className="max-w-7xl mx-auto px-6 flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-2">
          <Shield className="w-4 h-4 text-indigo-400" />
          <span>Intelligent Logistics & Delivery Optimization Platform (ILDO)</span>
          <span className="text-slate-600">|</span>
          <span>Enterprise Architecture</span>
        </div>
        <div className="flex items-center gap-4 text-slate-500">
          <span className="flex items-center gap-1.5">
            <Cpu className="w-3.5 h-3.5 text-slate-400" /> Python 3.13 / FastAPI
          </span>
          <span className="flex items-center gap-1.5">
            <Database className="w-3.5 h-3.5 text-slate-400" /> MySQL 8.0
          </span>
          <span className="flex items-center gap-1.5">
            <GitBranch className="w-3.5 h-3.5 text-slate-400" /> Phase 1 Foundation
          </span>
        </div>
      </div>
    </footer>
  );
}
