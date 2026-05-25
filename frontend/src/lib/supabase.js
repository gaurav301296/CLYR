/**
 * CLYR v2 — Supabase Client
 * Single source of truth for Supabase in the frontend.
 */
import { createClient } from '@supabase/supabase-js';
import { config } from '../config';

export const supabase = createClient(config.SUPABASE_URL, config.SUPABASE_ANON_KEY);

export function getSupabase() {
  return supabase;
}
