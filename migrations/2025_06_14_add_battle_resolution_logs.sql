CREATE TABLE public.battle_resolution_logs (
  resolution_id serial PRIMARY KEY,
  battle_type text NOT NULL CHECK (battle_type = ANY (ARRAY['kingdom','alliance'])),
  war_id integer REFERENCES public.wars_tactical(war_id),
  alliance_war_id integer REFERENCES public.alliance_wars(alliance_war_id),
  winner_side text NOT NULL CHECK (winner_side = ANY (ARRAY['attacker','defender','draw'])),
  total_ticks integer DEFAULT 0,
  attacker_casualties integer DEFAULT 0,
  defender_casualties integer DEFAULT 0,
  loot_summary jsonb DEFAULT '{}'::jsonb,
  created_at timestamp without time zone DEFAULT now()
);
