import React, { createContext, useContext, useEffect, useState } from 'react';
import { Session, User } from '@supabase/supabase-js';
import { supabase, isSupabaseConfigured } from '../../lib/supabase';

interface AuthContextType {
  session: Session | null;
  user: User | null;
  signOut: () => Promise<void>;
  signInDemo: () => void;
  isLoading: boolean;
  isDemo: boolean;
}

const DEMO_USER: User = {
  id: 'demo-user-finpulse',
  app_metadata: {},
  user_metadata: { full_name: 'Demo Investor' },
  aud: 'authenticated',
  created_at: new Date().toISOString(),
  email: 'investor@finpulse.ai',
  role: 'authenticated',
} as User;

const DEMO_SESSION: Session = {
  access_token: 'demo-guest-jwt-token',
  token_type: 'bearer',
  expires_in: 86400,
  refresh_token: 'demo-refresh',
  user: DEMO_USER,
} as Session;

const AuthContext = createContext<AuthContextType>({
  session: null,
  user: null,
  signOut: async () => {},
  signInDemo: () => {},
  isLoading: true,
  isDemo: false,
});

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [session, setSession] = useState<Session | null>(() => {
    const stored = localStorage.getItem('finpulse_demo_session');
    if (stored) {
      try {
        return JSON.parse(stored);
      } catch {
        return null;
      }
    }
    return null;
  });
  const [user, setUser] = useState<User | null>(() => session?.user ?? null);
  const [isLoading, setIsLoading] = useState(true);
  const [isDemo, setIsDemo] = useState<boolean>(() => Boolean(localStorage.getItem('finpulse_demo_session')));

  useEffect(() => {
    if (!isSupabaseConfigured) {
      // In unconfigured environments (e.g. Render build without Supabase credentials),
      // default to demo session so the app is immediately viewable and never stuck on a black screen.
      if (!session) {
        localStorage.setItem('finpulse_demo_session', JSON.stringify(DEMO_SESSION));
        setSession(DEMO_SESSION);
        setUser(DEMO_USER);
        setIsDemo(true);
      }
      setIsLoading(false);
      return;
    }

    supabase.auth.getSession().then(({ data: { session: currentSession } }) => {
      if (currentSession) {
        setSession(currentSession);
        setUser(currentSession.user);
        setIsDemo(false);
      } else {
        const stored = localStorage.getItem('finpulse_demo_session');
        if (stored) {
          try {
            const parsed = JSON.parse(stored);
            setSession(parsed);
            setUser(parsed.user);
            setIsDemo(true);
          } catch {
            setSession(null);
            setUser(null);
          }
        }
      }
      setIsLoading(false);
    }).catch(() => {
      setIsLoading(false);
    });

    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, newSession) => {
      if (newSession) {
        setSession(newSession);
        setUser(newSession.user);
        setIsDemo(false);
        localStorage.removeItem('finpulse_demo_session');
      } else {
        const stored = localStorage.getItem('finpulse_demo_session');
        if (stored) {
          try {
            const parsed = JSON.parse(stored);
            setSession(parsed);
            setUser(parsed.user);
            setIsDemo(true);
          } catch {
            setSession(null);
            setUser(null);
          }
        } else {
          setSession(null);
          setUser(null);
        }
      }
      setIsLoading(false);
    });

    return () => subscription.unsubscribe();
  }, []);

  const signInDemo = () => {
    localStorage.setItem('finpulse_demo_session', JSON.stringify(DEMO_SESSION));
    setSession(DEMO_SESSION);
    setUser(DEMO_USER);
    setIsDemo(true);
  };

  const signOut = async () => {
    localStorage.removeItem('finpulse_demo_session');
    setIsDemo(false);
    setSession(null);
    setUser(null);
    if (isSupabaseConfigured) {
      try {
        await supabase.auth.signOut();
      } catch {
        // Ignore network error on signout
      }
    }
  };

  return (
    <AuthContext.Provider value={{ session, user, signOut, signInDemo, isLoading, isDemo }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  return useContext(AuthContext);
};

