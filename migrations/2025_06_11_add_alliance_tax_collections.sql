-- Migration: add alliance_tax_collections table

CREATE TABLE public.alliance_tax_collections (
  collection_id SERIAL PRIMARY KEY,
  alliance_id INTEGER REFERENCES public.alliances(alliance_id),
  user_id UUID REFERENCES public.users(user_id),
  resource_type resource_type,
  amount_collected INTEGER,
  collected_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  source TEXT,
  notes TEXT
);

ALTER TABLE public.alliance_tax_collections ENABLE ROW LEVEL SECURITY;
CREATE POLICY access_own_alliance_tax ON public.alliance_tax_collections
  FOR ALL USING (
    EXISTS (
      SELECT 1 FROM public.alliance_members m
      WHERE m.alliance_id = alliance_tax_collections.alliance_id
        AND m.user_id = auth.uid()
    )
  ) WITH CHECK (
    EXISTS (
      SELECT 1 FROM public.alliance_members m
      WHERE m.alliance_id = alliance_tax_collections.alliance_id
        AND m.user_id = auth.uid()
    )
  );
