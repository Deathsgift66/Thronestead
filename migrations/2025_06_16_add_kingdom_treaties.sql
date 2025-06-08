-- Migration: add kingdom_treaties table
CREATE TABLE public.kingdom_treaties (
  treaty_id SERIAL PRIMARY KEY,
  kingdom_id INTEGER REFERENCES public.kingdoms(kingdom_id),
  treaty_type TEXT,
  partner_kingdom_id INTEGER REFERENCES public.kingdoms(kingdom_id),
  status TEXT CHECK (status IN ('proposed','active','cancelled')) DEFAULT 'proposed',
  signed_at TIMESTAMP WITH TIME ZONE
);
