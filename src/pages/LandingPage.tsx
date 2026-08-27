import React, { useEffect, useState } from 'react';
import { NavLink } from 'react-router-dom';
import { Activity, Shield, Brain, BarChart3, LineChart, ArrowRight, Zap, Lock, Sparkles } from 'lucide-react';

const STATS = [
  { label: 'Transactions Analyzed', target: 847200, suffix: '+' },
  { label: 'Forecast Accuracy', target: 97.3, suffix: '%' },
  { label: 'Anomalies Caught', target: 12400, suffix: '+' },
];

const AnimatedCounter: React.FC<{ target: number; suffix: string; duration?: number }> = ({ target, suffix, duration = 2000 }) => {
  const [count, setCount] = useState(0);
  useEffect(() => {
    let start = 0;
    const steps = 60;
    const increment = target / steps;
    let step = 0;
    const timer = setInterval(() => {
      step++;
      if (step >= steps) {
        setCount(target);
        clearInterval(timer);
      } else {
        const eased = 1 - Math.pow(1 - step / steps, 3);
        setCount(Math.round(start + (target - start) * eased * 10) / 10);
      }
    }, duration / steps);
    return () => clearInterval(timer);
  }, [target, duration]);

  return (
    <span className="font-mono font-bold text-2xl md:text-3xl text-white tabular-nums">
      {target >= 1000 ? Math.round(count).toLocaleString() : count.toFixed(1)}{suffix}
    </span>
  );
};

export const LandingPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-[#030303] text-[#ededed] font-sans overflow-x-hidden selection:bg-emerald-500/30 selection:text-emerald-200">
      {/* ═══ Navbar ═══ */}
      <nav className="fixed top-0 w-full z-50 border-b border-white/[0.04] bg-[#030303]/70 backdrop-blur-2xl">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="relative">
              <div className="w-7 h-7 bg-white flex items-center justify-center relative z-10 rounded-sm">
                <Activity className="w-4 h-4 text-black" strokeWidth={3} />
              </div>
              <div className="absolute inset-0 bg-white/20 animate-ring-pulse rounded-sm" />
            </div>
            <span className="text-sm font-bold tracking-tight">Finpluse</span>
          </div>
          <div className="flex items-center gap-6">
            <a href="#features" className="text-xs font-medium text-[#a1a1aa] hover:text-white transition-colors">Features</a>
            <a href="#stats" className="text-xs font-medium text-[#a1a1aa] hover:text-white transition-colors">Metrics</a>
            <NavLink to="/app" className="text-xs font-medium bg-white text-black px-5 py-2 rounded-lg hover:bg-[#e5e5e5] transition-all hover:scale-105 active:scale-95 btn-glow">
              Launch App
            </NavLink>
          </div>
        </div>
      </nav>

      {/* ═══ Hero Section ═══ */}
      <section className="pt-40 pb-32 px-6 relative overflow-hidden">
        {/* Animated background */}
        <div className="absolute inset-0 pointer-events-none">
          <div
            className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[900px] h-[900px] rounded-full animate-aurora"
            style={{
              background: 'radial-gradient(ellipse, rgba(16, 185, 129, 0.1) 0%, rgba(6, 182, 212, 0.05) 40%, transparent 70%)',
              filter: 'blur(80px)',
            }}
          />
          <div
            className="absolute top-1/3 right-1/4 w-[500px] h-[500px] rounded-full animate-aurora-2"
            style={{
              background: 'radial-gradient(ellipse, rgba(99, 102, 241, 0.08) 0%, transparent 70%)',
              filter: 'blur(60px)',
            }}
          />
          <div className="absolute inset-0 grid-pattern opacity-20" />
        </div>

        <div className="max-w-4xl mx-auto text-center relative z-10">
          {/* Status badge */}
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full glass-card-static mb-8 animate-fadeInDown">
            <span className="relative w-2 h-2">
              <span className="absolute inset-0 bg-emerald-400 rounded-full" />
              <span className="absolute inset-[-2px] border border-emerald-400/40 rounded-full animate-ring-pulse" />
            </span>
            <span className="text-xs font-medium text-[#a1a1aa]">Powered by Prophet & Isolation Forest</span>
          </div>

          {/* Headline with gradient */}
          <h1 className="text-5xl md:text-7xl lg:text-8xl font-bold tracking-tight mb-8 leading-[1.05] text-white font-display animate-fadeInUp">
            Intelligence for your <br />
            <span className="gradient-text-animated">
              capital.
            </span>
          </h1>
          <p className="text-lg text-[#a1a1aa] mb-12 max-w-2xl mx-auto leading-relaxed animate-fadeInUp stagger-2">
            Finpluse is a deterministic AI financial engine. We use mathematically verifiable models like Facebook Prophet and Enhanced Isolation Forests to understand your cash flow, with a Text-to-SQL RAG agent for zero-hallucination querying.
          </p>

          {/* CTA buttons */}
          <div className="flex items-center justify-center gap-4 animate-fadeInUp stagger-3">
            <NavLink
              to="/app"
              className="group relative px-8 py-4 bg-white text-black text-sm font-bold rounded-xl hover:bg-[#f0f0f0] transition-all hover:scale-105 active:scale-95 flex items-center gap-2 btn-glow"
            >
              Start Building Wealth
              <ArrowRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
            </NavLink>
            <NavLink
              to="/app/copilot"
              className="px-8 py-4 glass-card text-white text-sm font-medium rounded-xl flex items-center gap-2 hover:border-emerald-500/30 transition-all"
            >
              <Sparkles className="w-4 h-4 text-emerald-400" />
              Try AI Copilot
            </NavLink>
          </div>
        </div>
      </section>

      {/* ═══ Stats Ticker ═══ */}
      <section id="stats" className="py-16 px-6 border-t border-white/[0.04]">
        <div className="max-w-5xl mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {STATS.map((stat, i) => (
              <div key={i} className="text-center space-y-2 animate-fadeInUp" style={{ animationDelay: `${i * 0.1}s` }}>
                <AnimatedCounter target={stat.target} suffix={stat.suffix} />
                <p className="text-xs text-[#a1a1aa] font-mono uppercase tracking-wider">{stat.label}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ═══ Features Grid ═══ */}
      <section id="features" className="py-24 px-6 border-t border-white/[0.04]">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-white font-display mb-4">
              Built for <span className="gradient-text">precision</span>
            </h2>
            <p className="text-sm text-[#a1a1aa] max-w-lg mx-auto">
              Every component in Finpluse is engineered for mathematical accuracy and real-time intelligence.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-6">
            {[
              {
                icon: Brain,
                color: 'emerald',
                title: 'Zero-Hallucination Copilot',
                desc: 'Our conversational engine uses LLMs strictly for intent parsing, translating queries into deterministic SQL with strict schema guardrails.',
                gradient: 'from-emerald-500/10 to-cyan-500/5',
              },
              {
                icon: LineChart,
                color: 'indigo',
                title: 'Prophet Forecasting',
                desc: 'We utilize Facebook Prophet for time-series forecasting, capturing weekly seasonality and payday spikes to project your cash flow with mathematical confidence.',
                gradient: 'from-indigo-500/10 to-purple-500/5',
              },
              {
                icon: Shield,
                color: 'rose',
                title: 'Isolation Forest Security',
                desc: 'Every transaction is scored by an Enhanced Isolation Forest model in real-time, detecting multi-dimensional spending anomalies with 100% test recall.',
                gradient: 'from-rose-500/10 to-orange-500/5',
              },
            ].map((feature, i) => (
              <div
                key={i}
                className="glass-card rounded-2xl p-8 group animate-fadeInUp"
                style={{
                  animationDelay: `${i * 0.12}s`,
                  perspective: '1000px',
                }}
              >
                {/* Gradient hover overlay */}
                <div className={`absolute inset-0 rounded-2xl bg-gradient-to-br ${feature.gradient} opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none`} />
                
                <div className="relative z-10">
                  <div className={`w-12 h-12 rounded-xl bg-white/[0.04] border border-white/[0.06] flex items-center justify-center mb-6 group-hover:scale-110 group-hover:border-${feature.color}-500/30 transition-all duration-300`}>
                    <feature.icon className={`w-5 h-5 text-${feature.color}-400`} />
                  </div>
                  <h3 className="text-lg font-bold text-white mb-3">{feature.title}</h3>
                  <p className="text-sm text-[#a1a1aa] leading-relaxed">
                    {feature.desc}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ═══ Footer ═══ */}
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
