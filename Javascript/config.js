// Project Name: Kingmakers Rise©
// File Name: config.js
// Version 6.13.2025.19.49
// Developer: Deathsgift66
/*
  config.js — Public Supabase configuration (non-secret) used by frontend
  Automatically fallback to environment overrides if present (e.g., Render env vars)
*/

export const SUPABASE_URL = window.SUPABASE_URL || 'https://zzqoxgytfrbptojcwrjm.supabase.co';

// ❗ Public anon key — NEVER use service_role key in frontend.
export const SUPABASE_ANON_KEY = window.SUPABASE_ANON_KEY || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inp6cW94Z3l0ZnJicHRvamN3cmptIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDk1Nzk3MzYsImV4cCI6MjA2NTE1NTczNn0.mbFcI9V0ajn51SM68De5ox36VxbPEXK2WK978HZgUaE';

// Optional: Override API base URL (for FastAPI or Express proxy)
export const API_BASE_URL = window.API_BASE_URL || (location.port === '3000' ? 'http://localhost:8000' : '');
