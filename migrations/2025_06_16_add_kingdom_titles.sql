-- Migration: add kingdom_titles table and active_title column

CREATE TABLE public.kingdom_titles (
    kingdom_id INTEGER REFERENCES public.kingdoms(kingdom_id),
    title TEXT,
    awarded_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    PRIMARY KEY (kingdom_id, title)
);

ALTER TABLE public.kingdoms
    ADD COLUMN active_title TEXT;
