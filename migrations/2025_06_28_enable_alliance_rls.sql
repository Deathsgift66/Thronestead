-- Migration: enable row level security on alliance tables

ALTER TABLE public.alliances ENABLE ROW LEVEL SECURITY;
CREATE POLICY alliance_read_own ON public.alliances
  FOR SELECT USING (
    EXISTS (
      SELECT 1 FROM public.alliance_members m
      WHERE m.alliance_id = alliances.alliance_id
        AND m.user_id = auth.uid()
    )
  );

ALTER TABLE public.alliance_members ENABLE ROW LEVEL SECURITY;
CREATE POLICY alliance_members_self ON public.alliance_members
  FOR ALL USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

ALTER TABLE public.alliance_roles ENABLE ROW LEVEL SECURITY;
CREATE POLICY alliance_roles_read ON public.alliance_roles
  FOR SELECT USING (
    EXISTS (
      SELECT 1 FROM public.alliance_members m
      WHERE m.alliance_id = alliance_roles.alliance_id
        AND m.user_id = auth.uid()
    )
  );

ALTER TABLE public.alliance_vault ENABLE ROW LEVEL SECURITY;
CREATE POLICY alliance_vault_rw ON public.alliance_vault
  FOR ALL USING (
    EXISTS (
      SELECT 1 FROM public.alliance_members m
      WHERE m.alliance_id = alliance_vault.alliance_id
        AND m.user_id = auth.uid()
    )
  ) WITH CHECK (
    EXISTS (
      SELECT 1 FROM public.alliance_members m
      WHERE m.alliance_id = alliance_vault.alliance_id
        AND m.user_id = auth.uid()
    )
  );

ALTER TABLE public.alliance_vault_transaction_log ENABLE ROW LEVEL SECURITY;
CREATE POLICY alliance_vault_log_read ON public.alliance_vault_transaction_log
  FOR SELECT USING (
    EXISTS (
      SELECT 1 FROM public.alliance_members m
      WHERE m.alliance_id = alliance_vault_transaction_log.alliance_id
        AND m.user_id = auth.uid()
    )
  );

ALTER TABLE public.alliance_treaties ENABLE ROW LEVEL SECURITY;
CREATE POLICY alliance_treaties_access ON public.alliance_treaties
  FOR ALL USING (
    EXISTS (
      SELECT 1 FROM public.alliance_members m
      WHERE m.alliance_id IN (alliance_treaties.alliance_id, alliance_treaties.partner_alliance_id)
        AND m.user_id = auth.uid()
    )
  ) WITH CHECK (
    EXISTS (
      SELECT 1 FROM public.alliance_members m
      WHERE m.alliance_id = alliance_treaties.alliance_id
        AND m.user_id = auth.uid()
    )
  );

ALTER TABLE public.alliance_wars ENABLE ROW LEVEL SECURITY;
CREATE POLICY alliance_wars_access ON public.alliance_wars
  FOR SELECT USING (
    EXISTS (
      SELECT 1 FROM public.alliance_members m
      WHERE m.alliance_id IN (alliance_wars.attacker_alliance_id, alliance_wars.defender_alliance_id)
        AND m.user_id = auth.uid()
    )
  );
