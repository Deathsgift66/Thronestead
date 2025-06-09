-- Migration: add training_history table

CREATE TABLE public.training_history (
  history_id SERIAL PRIMARY KEY,
  kingdom_id INTEGER REFERENCES public.kingdoms(kingdom_id),
  unit_id INTEGER REFERENCES public.training_catalog(unit_id),
  unit_name TEXT,
  quantity INTEGER NOT NULL,
  completed_at TIMESTAMP WITH TIME ZONE,
  source TEXT,
  initiated_at TIMESTAMP WITH TIME ZONE,
  trained_by UUID REFERENCES public.users(user_id),
  xp_awarded INTEGER DEFAULT 0,
  modifiers_applied JSONB DEFAULT '{}'::jsonb
);

ALTER TABLE public.training_history ENABLE ROW LEVEL SECURITY;
CREATE POLICY access_own_training_history ON public.training_history
  FOR SELECT USING (
    auth.uid() = (
      SELECT user_id FROM public.kingdoms k
      WHERE k.kingdom_id = training_history.kingdom_id
    )
  );
