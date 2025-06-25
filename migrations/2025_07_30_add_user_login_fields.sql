-- Add sign_up_ip and last_login_at columns to users table
ALTER TABLE users ADD COLUMN IF NOT EXISTS sign_up_ip text;
ALTER TABLE users ADD COLUMN IF NOT EXISTS last_login_at timestamp with time zone;
