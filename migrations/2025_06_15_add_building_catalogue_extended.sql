-- Migration: expand building_catalogue with additional fields
DROP TABLE IF EXISTS public.building_catalogue CASCADE;
CREATE TABLE public.building_catalogue (
    building_id      SERIAL PRIMARY KEY,
    building_name    TEXT NOT NULL,
    description      TEXT,
    production_type  TEXT,
    production_rate  INTEGER,
    upkeep           INTEGER,
    build_cost       JSONB,
    modifiers        JSONB,
    category         TEXT,
    build_time_seconds INTEGER,
    prerequisites    JSONB,
    max_level        INTEGER,
    special_effects  JSONB,
    is_unique        BOOLEAN DEFAULT FALSE,
    is_repeatable    BOOLEAN DEFAULT FALSE,
    unlock_at_level  INTEGER DEFAULT 0,
    created_at       TIMESTAMPTZ DEFAULT now(),
    last_updated     TIMESTAMPTZ DEFAULT now()
);
