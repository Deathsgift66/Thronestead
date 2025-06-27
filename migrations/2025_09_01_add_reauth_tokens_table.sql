CREATE TABLE reauth_tokens (
  user_id uuid PRIMARY KEY REFERENCES users(user_id),
  token text NOT NULL,
  expires_at timestamptz NOT NULL,
  created_at timestamptz DEFAULT now()
);
