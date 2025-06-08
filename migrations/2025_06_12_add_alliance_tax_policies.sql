-- Migration: add alliance_tax_policies table

CREATE TABLE public.alliance_tax_policies (
  alliance_id INTEGER REFERENCES public.alliances(alliance_id),
  resource_type resource_type,
  tax_rate_percent NUMERIC(5,2) DEFAULT 0,
  is_active BOOLEAN DEFAULT TRUE,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  updated_by UUID REFERENCES public.users(user_id),
  PRIMARY KEY (alliance_id, resource_type)
);
