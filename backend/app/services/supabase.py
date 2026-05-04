from supabase import create_client, Client
from functools import lru_cache
from app.config import settings


@lru_cache()
def get_supabase() -> Client:
    """
    Returns a Supabase client singleton using the service role key.
    The service role key bypasses Row Level Security (RLS) for server-side operations.
    """
    client: Client = create_client(
        settings.supabase_url,
        settings.supabase_service_key,
    )
    return client


# Convenience singleton instance
supabase: Client = get_supabase()

# Added to trigger uvicorn reload
