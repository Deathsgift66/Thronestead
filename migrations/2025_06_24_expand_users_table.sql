-- Migration: expand users table with profile and status fields

ALTER TABLE public.users
  ADD COLUMN kingdom_name TEXT,
  ADD COLUMN profile_bio TEXT,
  ADD COLUMN profile_picture_url TEXT,
  ADD COLUMN region TEXT,
  ADD COLUMN kingdom_id INTEGER REFERENCES public.kingdoms(kingdom_id),
  ADD COLUMN alliance_id INTEGER REFERENCES public.alliances(alliance_id),
  ADD COLUMN alliance_role TEXT,
  ADD COLUMN active_policy INTEGER,
  ADD COLUMN active_laws INTEGER[] DEFAULT '{}'::integer[],
  ADD COLUMN is_admin BOOLEAN DEFAULT FALSE,
  ADD COLUMN is_banned BOOLEAN DEFAULT FALSE,
  ADD COLUMN is_deleted BOOLEAN DEFAULT FALSE,
  ADD COLUMN setup_complete BOOLEAN DEFAULT FALSE,
  ADD COLUMN sign_up_date DATE DEFAULT CURRENT_DATE,
  ADD COLUMN sign_up_time TIME WITH TIME ZONE DEFAULT CURRENT_TIME,
  ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();
