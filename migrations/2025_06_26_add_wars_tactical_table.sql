-- Migration: create wars_tactical table with tactical battle fields
CREATE TYPE war_phase AS ENUM ('alert', 'planning', 'live', 'resolved');
CREATE TYPE war_status AS ENUM ('active', 'paused', 'ended');

CREATE TABLE public.wars_tactical (
    war_id SERIAL PRIMARY KEY,
    attacker_kingdom_id INTEGER REFERENCES public.kingdoms(kingdom_id),
    defender_kingdom_id INTEGER REFERENCES public.kingdoms(kingdom_id),
    phase war_phase DEFAULT 'alert',
    castle_hp INTEGER DEFAULT 1000,
    battle_tick INTEGER DEFAULT 0,
    war_status war_status DEFAULT 'active',
    terrain_id INTEGER REFERENCES public.terrain_map(terrain_id),
    current_turn TEXT,
    attacker_score INTEGER DEFAULT 0,
    defender_score INTEGER DEFAULT 0,
    last_tick_processed_at TIMESTAMP WITH TIME ZONE,
    tick_interval_seconds INTEGER DEFAULT 300,
    is_concluded BOOLEAN DEFAULT FALSE,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    ended_at TIMESTAMP WITH TIME ZONE,
    fog_of_war BOOLEAN DEFAULT FALSE,
    weather TEXT,
    submitted_by UUID REFERENCES public.users(user_id)
);
