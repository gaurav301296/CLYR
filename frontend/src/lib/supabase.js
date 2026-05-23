// Supabase client — optional, only used if Supabase is configured
// For local development, auth uses the backend API directly

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || ''
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY || ''

export const supabase = null // Disabled for local dev — auth goes through backend API

export async function signUp(email, password, fullName = '') {
  throw new Error('Supabase not configured. Use backend auth API.')
}

export async function signIn(email, password) {
  throw new Error('Supabase not configured. Use backend auth API.')
}

export async function signOut() {
  // no-op
}

export async function getSession() {
  return { data: { session: null } }
}

export async function joinWaitlist(email, source = 'landing_page') {
  const res = await fetch(`${import.meta.env.VITE_API_BASE || 'http://localhost:8005/api'}/waitlist`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, source }),
  });
  return res.json();
}
