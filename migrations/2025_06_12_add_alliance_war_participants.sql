-- Migration: add alliance_war_participants table
CREATE TABLE public.alliance_war_participants (
  alliance_war_id integer REFERENCES public.alliance_wars(alliance_war_id) ON DELETE CASCADE,
  kingdom_id integer REFERENCES public.kingdoms(kingdom_id),
  role text CHECK (role IN ('attacker','defender')),
  PRIMARY KEY (alliance_war_id, kingdom_id)
);

CREATE INDEX alliance_war_participants_alliance_war_id_idx
  ON public.alliance_war_participants(alliance_war_id);
