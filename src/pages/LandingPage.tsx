import React from "react";
import { NavLink } from "react-router-dom";
import { ArrowRight, Activity, Shield, Brain, BarChart3, LineChart } from "lucide-react";

export const LandingPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-[#050505] text-[#ededed] font-sans overflow-x-hidden selection:bg-[#fff] selection:text-[#000]">
      {/* Navbar */}
      <nav className="fixed top-0 w-full z-50 border-b border-white/[0.04] bg-[#050505]/80 backdrop-blur-xl">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-sm bg-white flex items-center justify-center">
              <Activity className="w-4 h-4 text-black" strokeWidth={3} />
            </div>
            <span className="text-sm font-bold tracking-tight">Finpilot</span>
          </div>
          <div className="flex items-center gap-6">
            <a href="#features" className="text-xs font-medium text-[#a1a1aa] hover:text-white transition-colors">Features</a>
            <a href="#security" className="text-xs font-medium text-[#a1a1aa] hover:text-white transition-colors">Security</a>
            <NavLink to="/app" className="text-xs font-medium bg-white text-black px-4 py-2 rounded-full hover:bg-[#e5e5e5] transition-transform hover:scale-105 active:scale-95">
              Launch App
            </NavLink>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <main className="pt-40 pb-20 px-6 max-w-7xl mx-auto relative">
        {/* Subtle noise/gradient background */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[800px] bg-white/[0.02] rounded-full blur-[100px] pointer-events-none" />
        
        <div className="relative z-10 flex flex-col items-center text-center">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-white/[0.08] bg-white/[0.02] mb-8">
            <span className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse" />
            <span className="text-[11px] font-medium text-[#a1a1aa] uppercase tracking-widest">Finpilot is live</span>
          </div>
          
          <h1 className="text-5xl md:text-7xl lg:text-8xl font-medium tracking-tighter text-transparent bg-clip-text bg-gradient-to-b from-white to-white/60 max-w-5xl mx-auto leading-[1.05]">
            Intelligence for your capital.
          </h1>
          
          <p className="mt-8 text-[#a1a1aa] text-lg md:text-xl max-w-2xl mx-auto font-light leading-relaxed">
            Finpilot connects to your accounts and uses deterministic AI to model your cash flow, analyze anomalies, and project your 90-day runway. 
          </p>

          <div className="mt-12 flex items-center gap-4">
            <NavLink to="/app" className="group flex items-center gap-2 bg-white text-black px-6 py-3.5 rounded-full text-sm font-medium hover:bg-[#e5e5e5] transition-all">
              Open Dashboard
              <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
            </NavLink>
          </div>
        </div>

        {/* Bento Box Grid */}
        <div className="mt-32 grid grid-cols-1 md:grid-cols-3 gap-4" id="features">
          <div className="md:col-span-2 p-8 rounded-3xl bg-[#0a0a0a] border border-white/[0.04] relative overflow-hidden group hover:border-white/[0.08] transmition-colors">
            <div className="absolute top-0 right-0 w-64 h-64 bg-emerald-500/10 blur-[80px] group-hover:bg-emerald-500/20 transition-colors" />
            <Brain className="w-8 h-8 text-[#ededed] mb-12" strokeWidth={1.5} />
            <h3 className="text-2xl font-medium mb-3 text-white">Conversational AI Engine</h3>
            <p className="text-[#a1a1aa] max-w-md font-light leading-relaxed">
              Ask complex questions about your finances. Finpilot queries your real data and mathematically guarantees its answers. No hallucinations, just facts.
            </p>
          </div>
          
          <div className="p-8 rounded-3xl bg-[#0a0a0a] border border-white/[0.04] relative overflow-hidden group hover:border-white/[0.08] transition-colors">
            <div className="absolute top-0 right-0 w-32 h-32 bg-blue-500/10 blur-[60px] group-hover:bg-blue-500/20 transition-colors" />
            <LineChart className="w-8 h-8 text-[#ededed] mb-12" strokeWidth={1.5} />
            <h3 className="text-xl font-medium mb-3 text-white">90-Day Runway</h3>
            <p className="text-[#a1a1aa] font-light leading-relaxed text-sm">
              We project your recurring bills and income to forecast your future balance exactly.
            </p>
          </div>

          <div className="p-8 rounded-3xl bg-[#0a0a0a] border border-white/[0.04] relative overflow-hidden group hover:border-white/[0.08] transition-colors">
            <BarChart3 className="w-8 h-8 text-[#ededed] mb-12" strokeWidth={1.5} />
            <h3 className="text-xl font-medium mb-3 text-white">Anomaly Detection</h3>
            <p className="text-[#a1a1aa] font-light leading-relaxed text-sm">
              Automatically flagged statistical spikes in category spending.
            </p>
          </div>

          <div className="md:col-span-2 p-8 rounded-3xl bg-[#0a0a0a] border border-white/[0.04] relative overflow-hidden group hover:border-white/[0.08] transition-colors" id="security">
            <div className="absolute top-0 right-0 w-64 h-64 bg-orange-500/10 blur-[80px] group-hover:bg-orange-500/20 transition-colors" />
            <Shield className="w-8 h-8 text-[#ededed] mb-12" strokeWidth={1.5} />
            <h3 className="text-2xl font-medium mb-3 text-white">Bank-Grade Privacy</h3>
            <p className="text-[#a1a1aa] max-w-md font-light leading-relaxed">
              Read-only connections. End-to-end encryption. Your data is analyzed locally on the server and never sold to third parties. We don't have access to move your money.
            </p>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-white/[0.04] mt-20">
        <div className="max-w-7xl mx-auto px-6 py-12 flex flex-col md:flex-row justify-between items-center gap-4">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-[2px] bg-white flex items-center justify-center">
              <Activity className="w-3 h-3 text-black" strokeWidth={4} />
            </div>
            <span className="text-xs font-bold tracking-tight text-white">Finpilot</span>
          </div>
          <div className="text-xs text-[#666] font-light">
            © 2026 Finpilot AI.
          </div>
        </div>
      </footer>
    </div>
  );
};