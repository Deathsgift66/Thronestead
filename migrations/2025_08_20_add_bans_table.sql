CREATE TABLE public.bans (
  ban_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid REFERENCES public.users(user_id),
  ip_address text,
  device_hash text,
  ban_type text NOT NULL CHECK (ban_type IN ('ip', 'device', 'account', 'other')),
  reason text,
  issued_by uuid REFERENCES public.users(user_id),
  issued_at timestamptz DEFAULT now(),
  expires_at timestamptz,
  is_active boolean DEFAULT true,
  notes text
);
