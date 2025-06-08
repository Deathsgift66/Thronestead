CREATE TABLE public.alliance_war_combat_logs (
  combat_id bigserial PRIMARY KEY,
  alliance_war_id integer REFERENCES public.alliance_wars(alliance_war_id) ON DELETE CASCADE,
  tick_number integer NOT NULL,
  event_type text NOT NULL,
  attacker_unit_id integer,
  defender_unit_id integer,
  position_x integer,
  position_y integer,
  damage_dealt integer DEFAULT 0,
  morale_shift double precision DEFAULT 0,
  notes text,
  timestamp timestamp without time zone DEFAULT now()
);

CREATE INDEX alliance_war_combat_logs_alliance_war_id_idx ON public.alliance_war_combat_logs(alliance_war_id);
