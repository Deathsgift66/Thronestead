CREATE TABLE IF NOT EXISTS alliance_loan_repayments (
    schedule_id SERIAL PRIMARY KEY,
    loan_id integer REFERENCES alliance_loans(loan_id),
    due_date timestamp with time zone,
    amount_due bigint DEFAULT 0,
    amount_paid bigint DEFAULT 0,
    paid_at timestamp with time zone,
    status text DEFAULT 'pending' CHECK (status IN ('pending','paid','missed'))
);
CREATE INDEX IF NOT EXISTS idx_alliance_loan_repayments_loan_id ON alliance_loan_repayments(loan_id);
