#!/bin/bash
set -e
export PYTHONPATH=$(pwd)

# Load overrides from .env.test if present
if [ -f ".env.test" ]; then
    set -a
    source .env.test
    set +a
fi

: "${SUPABASE_URL:=https://test.supabase.co}"
: "${SUPABASE_ANON_KEY:=test-anon-key}"
: "${SUPABASE_SERVICE_ROLE_KEY:=test-service-role}"
: "${DATABASE_URL:=postgresql://test_user:test_pass@localhost/test_db}"

pytest -q "$@"
