from supabase import Client, create_client


def get_supabase_client(app) -> Client:
    url = app.config.get("SUPABASE_URL")
    key = app.config.get("SUPABASE_KEY")

    if not url or not key:
        raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set")

    return create_client(url, key)
