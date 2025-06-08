-- Migration: add kingdom_spies table

CREATE TABLE public.kingdom_spies (
  kingdom_id INTEGER PRIMARY KEY REFERENCES public.kingdoms(kingdom_id),
  spy_level INTEGER DEFAULT 1,
  spy_count INTEGER DEFAULT 0,
  max_spy_capacity INTEGER DEFAULT 0,
  spy_xp INTEGER DEFAULT 0,
  spy_upkeep_gold INTEGER DEFAULT 0,
  last_mission_at TIMESTAMP WITH TIME ZONE,
  cooldown_seconds INTEGER DEFAULT 0,
  spies_lost INTEGER DEFAULT 0,
  missions_attempted INTEGER DEFAULT 0,
  missions_successful INTEGER DEFAULT 0,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
  last_updated TIMESTAMP WITH TIME ZONE DEFAULT now()
);
