import os


def get_supabase_client():
    """Return a configured Supabase client or raise if unavailable."""
    try:  # pragma: no cover - optional dependency
        from supabase import create_client
    except ImportError as e:  # pragma: no cover - library missing
        raise RuntimeError("supabase client library not installed") from e

    url = os.getenv("SUPABASE_URL")
    key = (
        os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        or os.getenv("SUPABASE_KEY")
        or os.getenv("SUPABASE_ANON_KEY")
    )
    if not url or not key:
        raise RuntimeError("Supabase credentials not configured")

    return create_client(url, key)
