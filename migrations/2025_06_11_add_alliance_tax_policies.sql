-- Migration: add alliance_tax_policies table
CREATE TABLE public.alliance_tax_policies (
  alliance_id integer REFERENCES public.alliances(alliance_id),
  resource_type resource_type,
  tax_rate_percent numeric(5,2) NOT NULL,
  is_active boolean DEFAULT true,
  updated_at timestamp with time zone DEFAULT now(),
  updated_by uuid REFERENCES public.users(user_id),
  PRIMARY KEY (alliance_id, resource_type)
);
