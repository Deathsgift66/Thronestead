// Project Name: Thronestead©
// File Name: env.example.js
// Version 6.13.2025.19.49
// Developer: Deathsgift66

/**
 * This file is an example template.
 * Copy it to `env.js` and insert your actual Supabase project credentials.
 * DO NOT commit real `env.js` to version control (it should be in .gitignore).
 */

// Example values used by the frontend during local development.
// Copy this file to `env.js` and replace with your real credentials.

export const SUPABASE_URL = 'https://your-project.supabase.co';
export const SUPABASE_ANON_KEY = 'your-anon-key';

// Optional: Override API base URL for local development
export const VITE_API_BASE_URL = 'http://localhost:8000';


// Support the previous window.ENV style for backward compatibility
window.ENV = {
  VITE_SUPABASE_URL: SUPABASE_URL,
  VITE_SUPABASE_ANON_KEY: SUPABASE_ANON_KEY,
  VITE_API_BASE_URL

};
