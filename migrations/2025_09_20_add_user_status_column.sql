-- Add status column to users table to track account state
ALTER TABLE users ADD COLUMN IF NOT EXISTS status text DEFAULT 'active';
