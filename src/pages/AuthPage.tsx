import React, { useState } from "react";
import { supabase } from "../lib/supabase";
import { Activity, Lock, Mail, User, ArrowRight } from "lucide-react";
import { Navigate } from "react-router-dom";
import { useAuth } from "../components/layout/AuthProvider";

export const AuthPage: React.FC = () => {
  const { session } = useAuth();
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  if (session) {
    return <Navigate to="/app" replace />;
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      if (isLogin) {
        const { error } = await supabase.auth.signInWithPassword({
          email,
          password,
        });
        if (error) throw error;
      } else {
        const { error } = await supabase.auth.signUp({
          email,
          password,
          options: {
            data: { full_name: fullName },
            emailRedirectTo: `${window.location.origin}/app`,
          },
        });
        if (error) throw error;
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#030303] text-[#ededed] font-sans flex flex-col items-center justify-center p-4 relative overflow-hidden">
      {/* Animated background */}
      <div className="absolute inset-0 pointer-events-none">
        <div
          className="absolute top-1/4 left-1/3 w-[600px] h-[600px] rounded-full animate-aurora"
          style={{
            background: 'radial-gradient(ellipse, rgba(16, 185, 129, 0.07) 0%, transparent 70%)',
            filter: 'blur(80px)',
          }}
        />
        <div
          className="absolute bottom-1/4 right-1/3 w-[500px] h-[500px] rounded-full animate-aurora-2"
          style={{
            background: 'radial-gradient(ellipse, rgba(99, 102, 241, 0.06) 0%, transparent 70%)',
            filter: 'blur(70px)',
          }}
        />
        <div className="absolute inset-0 grid-pattern opacity-20" />
      </div>

      {/* Brand */}
      <div className="top-6 left-8 absolute z-10">
        <div className="flex items-center gap-2.5">
          <div className="relative">
            <div className="w-7 h-7 bg-white flex items-center justify-center rounded-sm relative z-10">
              <Activity className="w-4 h-4 text-black" strokeWidth={3} />
            </div>
            <div className="absolute inset-0 bg-white/20 animate-ring-pulse rounded-sm" />
          </div>
          <span className="text-sm font-bold tracking-tight">Finpluse</span>
        </div>
      </div>

      {/* Auth Card */}
      <div className="w-full max-w-md glass-card rounded-2xl p-8 relative z-10 animate-scaleIn">
        {/* Top glow line */}
        <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-emerald-500/40 to-transparent" />
        
        {/* Corner markers */}
        <div className="absolute top-0 left-0 w-4 h-4 border-t border-l border-emerald-500/30" />
        <div className="absolute top-0 right-0 w-4 h-4 border-t border-r border-emerald-500/30" />
        <div className="absolute bottom-0 left-0 w-4 h-4 border-b border-l border-white/[0.06]" />
        <div className="absolute bottom-0 right-0 w-4 h-4 border-b border-r border-white/[0.06]" />

        <h1 className="text-2xl font-bold mb-2 text-white font-display">
          {isLogin ? "Welcome back" : "Create account"}
        </h1>
        <p className="text-[#a1a1aa] text-sm mb-8">
          {isLogin
            ? "Enter your details to access your financial copilot."
            : "Get started with intelligence for your capital."}
        </p>

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          {!isLogin && (
            <div className="animate-fadeInUp">
              <label className="block text-[#a1a1aa] text-xs mb-1.5 font-medium">Full Name</label>
              <div className="relative">
                <User className="w-4 h-4 text-[#52525b] absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  className="w-full bg-white/[0.03] border border-white/[0.08] rounded-xl pl-10 pr-4 py-2.5 text-sm text-white input-glow transition-all"
                  required
                  placeholder="Your full name"
                />
              </div>
            </div>
          )}
          <div>
            <label className="block text-[#a1a1aa] text-xs mb-1.5 font-medium">Email</label>
            <div className="relative">
              <Mail className="w-4 h-4 text-[#52525b] absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full bg-white/[0.03] border border-white/[0.08] rounded-xl pl-10 pr-4 py-2.5 text-sm text-white input-glow transition-all"
                required
                placeholder="you@example.com"
              />
            </div>
          </div>
          <div>
            <label className="block text-[#a1a1aa] text-xs mb-1.5 font-medium">Password</label>
            <div className="relative">
              <Lock className="w-4 h-4 text-[#52525b] absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full bg-white/[0.03] border border-white/[0.08] rounded-xl pl-10 pr-4 py-2.5 text-sm text-white input-glow transition-all"
                required
                placeholder="••••••••"
              />
            </div>
          </div>

          {error && (
            <div className="px-3 py-2 bg-rose-500/10 border border-rose-500/20 rounded-xl animate-fadeIn">
              <p className="text-rose-400 text-xs">{error}</p>
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="mt-2 w-full bg-white text-black py-3 rounded-xl text-sm font-bold hover:bg-[#e5e5e5] transition-all disabled:opacity-50 btn-glow flex items-center justify-center gap-2 group"
          >
            {loading ? (
              <div className="w-4 h-4 border-2 border-black/20 border-t-black rounded-full animate-spin" />
            ) : (
              <>
                {isLogin ? "Sign In" : "Create Account"}
                <ArrowRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
              </>
            )}
          </button>

          <div className="text-center mt-4">
            <button
              type="button"
              onClick={() => setIsLogin(!isLogin)}
              className="text-xs text-[#a1a1aa] hover:text-white transition-colors"
            >
              {isLogin
                ? "Don't have an account? Sign up"
                : "Already have an account? Sign in"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};