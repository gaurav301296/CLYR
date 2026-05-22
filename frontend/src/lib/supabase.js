import { createClient } from '@supabase/supabase-js';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || '';
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY || '';

// Only create client if both URL and key are provided and not placeholders
export const supabase = (supabaseUrl && supabaseAnonKey && !supabaseUrl.includes('placeholder'))
  ? createClient(supabaseUrl, supabaseAnonKey)
  : null;

export async function signUp(email, password, fullName = '') {
  if (!supabase) throw new Error('Supabase not configured');
  return supabase.auth.signUp({ email, password, options: { data: { full_name: fullName } } });
}

export async function signIn(email, password) {
  if (!supabase) throw new Error('Supabase not configured');
  return supabase.auth.signInWithPassword({ email, password });
}

export async function signOut() {
  if (!supabase) return;
  return supabase.auth.signOut();
}

export async function getSession() {
  if (!supabase) return { data: { session: null } };
  return supabase.auth.getSession();
}

export async function joinWaitlist(email, source = 'landing_page') {
  if (!supabase) return { message: 'Supabase not configured' };
  const res = await fetch(`${import.meta.env.VITE_API_BASE || 'http://localhost:8005/api'}/waitlist`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, source }),
  });
  return res.json();
}
