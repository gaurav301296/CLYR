import os
from supabase import create_client, Client

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY", "")

_supabase: Client | None = None
_supabase_admin: Client | None = None


def get_supabase() -> Client:
    """Get Supabase client with anon key (for client-side operations)."""
    global _supabase
    if _supabase is None:
        _supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    return _supabase


def get_supabase_admin() -> Client:
    """Get Supabase admin client with service role key (for server-side operations)."""
    global _supabase_admin
    if _supabase_admin is None:
        _supabase_admin = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _supabase_admin
