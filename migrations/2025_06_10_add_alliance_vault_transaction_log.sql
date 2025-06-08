CREATE TABLE public.alliance_vault_transaction_log (
  transaction_id bigserial PRIMARY KEY,
  alliance_id integer REFERENCES public.alliances(alliance_id),
  user_id uuid REFERENCES public.users(user_id),
  action text NOT NULL CHECK (action IN ('deposit','withdraw','transfer','trade')),
  resource_type text NOT NULL,
  amount bigint NOT NULL,
  notes text,
  created_at timestamp with time zone DEFAULT now()
);

CREATE INDEX alliance_vault_transaction_log_alliance_id_idx ON public.alliance_vault_transaction_log(alliance_id);
