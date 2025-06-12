-- Migration: add security settings fields to users table
ALTER TABLE public.users
  ADD COLUMN last_login_at TIMESTAMP WITH TIME ZONE,
  ADD COLUMN last_login_ip TEXT,
  ADD COLUMN ip_login_alerts BOOLEAN DEFAULT FALSE,
  ADD COLUMN email_login_confirmations BOOLEAN DEFAULT FALSE;
