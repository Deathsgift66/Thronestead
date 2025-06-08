CREATE TABLE public.alliance_war_scores (
  alliance_war_id integer PRIMARY KEY REFERENCES public.alliance_wars(alliance_war_id) ON DELETE CASCADE,
  attacker_score integer DEFAULT 0,
  defender_score integer DEFAULT 0,
  victor text CHECK (victor = ANY (ARRAY['attacker', 'defender', 'draw'])),
  last_updated timestamp without time zone DEFAULT now()
);
