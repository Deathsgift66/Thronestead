-- Migration: expand kingdom_troop_slots with additional slot and morale columns
ALTER TABLE public.kingdom_troop_slots
  ADD COLUMN slots_from_buildings integer DEFAULT 0,
  ADD COLUMN slots_from_tech integer DEFAULT 0,
  ADD COLUMN slots_from_projects integer DEFAULT 0,
  ADD COLUMN slots_from_events integer DEFAULT 0,
  ADD COLUMN morale_bonus_buildings integer DEFAULT 0,
  ADD COLUMN morale_bonus_tech integer DEFAULT 0,
  ADD COLUMN morale_bonus_events integer DEFAULT 0,
  ADD COLUMN last_morale_update timestamp with time zone DEFAULT now(),
  ADD COLUMN morale_cooldown_seconds integer DEFAULT 0,
  ADD COLUMN last_in_combat_at timestamp with time zone,
  ADD COLUMN currently_in_combat boolean DEFAULT false,
  ADD COLUMN created_at timestamp with time zone DEFAULT now(),
  ADD COLUMN last_updated timestamp with time zone DEFAULT now();
