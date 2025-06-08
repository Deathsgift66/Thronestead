-- Migration: add alliance_treaties table
CREATE TABLE public.alliance_treaties (
  treaty_id SERIAL PRIMARY KEY,
  alliance_id INTEGER REFERENCES public.alliances(alliance_id),
  treaty_type TEXT,
  partner_alliance_id INTEGER REFERENCES public.alliances(alliance_id),
  status TEXT CHECK (status IN ('proposed','active','cancelled')) DEFAULT 'proposed',
  signed_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);
