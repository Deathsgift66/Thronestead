-- Migration: add black_market_listings table

CREATE TABLE public.black_market_listings (
  listing_id SERIAL PRIMARY KEY,
  seller_id UUID REFERENCES public.users(user_id),
  item TEXT,
  price NUMERIC,
  quantity INTEGER,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE INDEX idx_black_market_listings_seller ON public.black_market_listings (seller_id);

ALTER TABLE public.black_market_listings ENABLE ROW LEVEL SECURITY;
CREATE POLICY access_own_black_market_listings ON public.black_market_listings
  FOR ALL USING (auth.uid() = seller_id)
  WITH CHECK (auth.uid() = seller_id);
