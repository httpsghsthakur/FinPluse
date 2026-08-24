import React, { useState } from "react";
import { supabase } from "../lib/supabase";
import { Activity } from "lucide-react";
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
    <div className="min-h-screen bg-[#050505] text-[#ededed] font-sans flex flex-col items-center justify-center p-4">
      <div className="top-4 left-8 absolute">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded-sm bg-white flex items-center justify-center">
            <Activity className="w-4 h-4 text-black" strokeWidth={3} />
          </div>
          <span className="text-sm font-bold tracking-tight">Finpluse</span>
        </div>
      </div>

      <div className="w-full max-w-md p-8 rounded-3xl bg-[#0a0a0a] border border-white/[0.04] relative overflow-hidden">
        <div className="absolute top-0 right-0 w-64 h-64 bg-blue-500/5 blur-[80px] pointer-events-none" />
        <h1 className="text-2xl font-medium mb-2 text-white">
          {isLogin ? "Welcome to Finpluse" : "Create account"}
        </h1>
        <p className="text-[#a1a1aa] text-sm mb-8">
          {isLogin
            ? "Enter your details to access your financial copilot."
            : "Get started with intelligence for your capital."}
        </p>

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          (!isLogin && (
            <div>
              <label className="block text-[#a1a1aa] text-xs mb-1.5">Full Name</label>
              <input
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                className="w-full bg-[#141414] border border-white/[0.08] rounded-lg px-4 py-2.5 text-sm text-white focus:outline-none focus:border-white/20"
                required
              />
            </div>
          ))
          <div>
            <label className="block text-[#a1a1aa] text-xs mb-1.5">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full bg-[#141414] border border-white/[0.08] rounded-lg px-4 py-2.5 text-sm text-white focus:outline-none focus:border-white/20"
              required
            />
          </div>
          <div>
            <label className="block text-[#a1a1aa] text-xs mb-1.5">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full bg-[#141414] border border-white/[0.08] rounded-lg px-4 py-2.5 text-sm text-white focus:outline-none focus:border-white/20"
              required
            />
          </div>

          {error && (
            <div className="px-3 py-2 bg-red-500/10 border border-red-500/20 rounded-md">
              <p className="text-red-400 text-xs">{error}</p>
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="mt-2 w-full bg-white text-black py-2.5 rounded-lg text-sm font-medium hover:bg-[#e5e5e5] transition-colors disabled:opacity-50"
          >
            {loading ? "Please wait..." : (isLogin ? "Sign In" : "Create Account")}
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