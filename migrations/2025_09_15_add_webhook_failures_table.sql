-- Table to store failed webhook deliveries for retry processing
CREATE TABLE IF NOT EXISTS webhook_failures (
  failure_id serial PRIMARY KEY,
  hook_name text,
  endpoint_url text,
  payload jsonb,
  attempt_count integer DEFAULT 0,
  last_error text,
  next_attempt_at timestamptz DEFAULT now(),
  created_at timestamptz DEFAULT now()
);
