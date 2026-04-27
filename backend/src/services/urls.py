from urllib.parse import urlparse, urlunparse, quote, parse_qs, urlencode

def to_psycopg_conninfo(database_url: str) -> str:
    """
    Fix for AWS RDS + psycopg3:
    - Automatically URL-encodes the password (handles # $ ^ ! % * etc.)
    - Ensures ?sslmode=require is always present
    - Works whether the password in Secrets Manager is raw or already encoded
    """
    if not database_url or not database_url.strip():
        return database_url.strip()

    u = database_url.strip()

    # Normalize prefixes
    u = u.replace("postgres://", "postgresql://", 1)
    u = u.replace("postgresql+asyncpg://", "postgresql://", 1)

    parsed = urlparse(u)

    # Re-encode password safely
    if parsed.password:
        safe_password = quote(parsed.password, safe="")   # This is the key fix
        netloc = parsed.netloc.replace(parsed.password, safe_password, 1)
        parsed = parsed._replace(netloc=netloc)

    # Force sslmode=require for RDS
    query_params = parse_qs(parsed.query, keep_blank_values=True)
    query_params["sslmode"] = ["require"]

    new_query = urlencode(query_params, doseq=True)
    parsed = parsed._replace(query=new_query)

    return urlunparse(parsed)