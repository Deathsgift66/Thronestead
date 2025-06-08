-- Migration: Add regions support

-- Ensure kingdoms has region column
ALTER TABLE public.kingdoms
  ADD COLUMN IF NOT EXISTS region text;

-- Catalogue of available regions
CREATE TABLE public.region_catalogue (
  region_code text PRIMARY KEY,
  name text,
  description text,
  resource_bonus jsonb DEFAULT '{}',
  troop_bonus integer DEFAULT 0
);

-- Sample starter regions
INSERT INTO public.region_catalogue (region_code, name, description, resource_bonus, troop_bonus) VALUES
  ('north', 'Northlands', 'Cold and rugged with hardy people.', '{"wood":50}', 2),
  ('south', 'Southlands', 'Fertile fields and warm climate.', '{"food":100}', 1),
  ('east', 'Eastreach', 'Rich trade routes and culture.', '{"gold":20}', 3),
  ('west', 'Westvale', 'Frontier lands full of stone.', '{"stone":50}', 0);
