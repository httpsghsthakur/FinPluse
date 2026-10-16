import { createClient } from '@supabase/supabase-js';

const rawUrl = import.meta.env.VITE_SUPABASE_URL;
const rawKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

export const isSupabaseConfigured = Boolean(
  rawUrl &&
  rawKey &&
  typeof rawUrl === 'string' &&
  rawUrl.trim() !== '' &&
  !rawUrl.includes('example.com') &&
  !rawUrl.includes('placeholder')
);

// Safe fallback credentials so that createClient never throws "supabaseUrl is required"
// during bundle evaluation if env variables are missing at build time.
const fallbackUrl = 'https://placeholder.supabase.co';
const fallbackKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.e30.placeholder';

export const supabase = createClient(
  isSupabaseConfigured ? rawUrl : fallbackUrl,
  isSupabaseConfigured ? rawKey : fallbackKey
);

export const supabaseAuth = {
  getHeaders: async () => {
    if (!isSupabaseConfigured) {
      // Well-formed 3-part JWT for local demo development
      const defaultDemoToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJkZW1vLXVzZXItMTIzIiwibmFtZSI6IkZpblB1bHNlIERlbW8gVXNlciIsImVtYWlsIjoiZGVtb0BmaW5wdWxzZS5haSJ9.mock-signature';
      const stored = localStorage.getItem('finpulse_demo_token');
      const demoToken = (stored && stored.count && stored.split('.').length === 3) ? stored : defaultDemoToken;
      return { Authorization: 'Bearer ' + demoToken };
    }
    try {
      const { data: { session } } = await supabase.auth.getSession();
      if (session?.access_token) {
        return { Authorization: 'Bearer ' + session.access_token };
      }
    } catch {
      // Fallback
    }
    return {
      Authorization: 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJkZW1vLXVzZXItMTIzIiwibmFtZSI6IkZpblB1bHNlIERlbW8gVXNlciIsImVtYWlsIjoiZGVtb0BmaW5wdWxzZS5haSJ9.mock-signature'
    };
  }
};

