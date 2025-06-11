-- Migration: expand projects_alliance with runtime tracking fields

ALTER TABLE public.projects_alliance
  ADD COLUMN project_key text REFERENCES project_alliance_catalogue(project_key),
  ADD COLUMN modifiers jsonb DEFAULT '{}'::jsonb,
  ADD COLUMN start_time timestamp with time zone DEFAULT now(),
  ADD COLUMN end_time timestamp with time zone,
  ADD COLUMN is_active boolean DEFAULT false,
  ADD COLUMN build_state text CHECK (build_state IN ('queued','building','completed','expired')) DEFAULT 'queued',
  ADD COLUMN built_by uuid REFERENCES users(user_id),
  ADD COLUMN expires_at timestamp with time zone,
  ADD COLUMN last_updated timestamp with time zone DEFAULT now();
