import React from 'react';
import { NavLink } from 'react-router-dom';
import { Activity, Shield, Brain, BarChart3, LineChart } from 'lucide-react';

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
            <span className="text-sm font-bold tracking-tight">Finpluse</span>
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
      <section className="pt-40 pb-32 px-6 relative">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-blue-500/10 blur-[120px] rounded-full pointer-events-none" />
        <div className="max-w-4xl mx-auto text-center relative z-10">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/[0.03] border border-white/[0.08] mb-8">
            <span className="w-2 h-2 rounded-full bg-blue-500 animate-pulse" />
            <span className="text-xs font-medium text-[#a1a1aa]">Powered by Prophet & Isolation Forest</span>
          </div>
          <h1 className="text-5xl md:text-7xl font-medium tracking-tight mb-8 leading-[1.1] text-white">
            Intelligence for your <br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-indigo-400">
              capital.
            </span>
          </h1>
          <p className="text-lg text-[#a1a1aa] mb-12 max-w-2xl mx-auto leading-relaxed">
            Finpluse is a deterministic AI financial engine. We use mathematically verifiable models like Facebook Prophet and Enhanced Isolation Forests to understand your cash flow, with a Text-to-SQL RAG agent for zero-hallucination querying.
          </p>
          <div className="flex items-center justify-center gap-4">
            <NavLink to="/app" className="px-8 py-4 rounded-full bg-white text-black text-sm font-medium hover:bg-[#e5e5e5] transition-transform hover:scale-105 active:scale-95">
              Start Building Wealth
            </NavLink>
          </div>
        </div>
      </section>

      {/* Features Grid */}
      <section id="features" className="py-24 px-6 border-t border-white/[0.04]">
        <div className="max-w-7xl mx-auto">
          <div className="grid md:grid-cols-3 gap-6">
            <div className="p-8 rounded-3xl bg-[#0a0a0a] border border-white/[0.04] group hover:border-white/[0.1] transition-colors relative overflow-hidden">
              <div className="absolute top-0 right-0 w-32 h-32 bg-blue-500/5 blur-[40px] rounded-full group-hover:bg-blue-500/10 transition-colors" />
              <div className="w-12 h-12 rounded-xl bg-[#141414] border border-white/[0.08] flex items-center justify-center mb-6 relative z-10">
                <Brain className="w-5 h-5 text-blue-400" />
              </div>
              <h3 className="text-lg font-medium text-white mb-3 relative z-10">Zero-Hallucination Copilot</h3>
              <p className="text-sm text-[#a1a1aa] leading-relaxed relative z-10">
                Our conversational engine uses LLMs strictly for intent parsing, translating queries into deterministic SQL with strict schema guardrails.
              </p>
            </div>
            
            <div className="p-8 rounded-3xl bg-[#0a0a0a] border border-white/[0.04] group hover:border-white/[0.1] transition-colors relative overflow-hidden">
              <div className="absolute top-0 right-0 w-32 h-32 bg-indigo-500/5 blur-[40px] rounded-full group-hover:bg-indigo-500/10 transition-colors" />
              <div className="w-12 h-12 rounded-xl bg-[#141414] border border-white/[0.08] flex items-center justify-center mb-6 relative z-10">
                <LineChart className="w-5 h-5 text-indigo-400" />
              </div>
              <h3 className="text-lg font-medium text-white mb-3 relative z-10">Prophet Forecasting</h3>
              <p className="text-sm text-[#a1a1aa] leading-relaxed relative z-10">
                We utilize Facebook Prophet for time-series forecasting, capturing weekly seasonality and payday spikes to project your cash flow with mathematical confidence.
              </p>
            </div>
            
            <div className="p-8 rounded-3xl bg-[#0a0a0a] border border-white/[0.04] group hover:border-white/[0.1] transition-colors relative overflow-hidden">
              <div className="absolute top-0 right-0 w-32 h-32 bg-rose-500/5 blur-[40px] rounded-full group-hover:bg-rose-500/10 transition-colors" />
              <div className="w-12 h-12 rounded-xl bg-[#141414] border border-white/[0.08] flex items-center justify-center mb-6 relative z-10">
                <Shield className="w-5 h-5 text-rose-400" />
              </div>
              <h3 className="text-lg font-medium text-white mb-3 relative z-10">Isolation Forest Security</h3>
              <p className="text-sm text-[#a1a1aa] leading-relaxed relative z-10">
                Every transaction is scored by an Enhanced Isolation Forest model in real-time, detecting multi-dimensional spending anomalies with 100% test recall.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 px-6 border-t border-white/[0.04]">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <Activity className="w-4 h-4 text-[#a1a1aa]" />
            <span className="text-sm font-medium text-[#a1a1aa]">Finpluse AI</span>
          </div>
          <p className="text-xs text-[#52525b]">
            Designed for engineers. Built for scale.
          </p>
        </div>
      </footer>
    </div>
  );
};
