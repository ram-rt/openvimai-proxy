import duckdb, hashlib
from datetime import datetime, timedelta
from core.settings import settings

con = duckdb.connect(settings.cache_db, read_only=False)
con.execute("""
CREATE TABLE IF NOT EXISTS cache (
    prompt_hash VARCHAR PRIMARY KEY,
    response   VARCHAR,
    tokens     INT,
    created_at TIMESTAMP
)
""")
TTL = timedelta(minutes=settings.cache_ttl_minutes)

def _hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()

def _purge_expired() -> None:
    cutoff = datetime.now() - TTL
    con.execute("DELETE FROM cache WHERE created_at < ?", (cutoff,))

def get(prompt: str):
    h = _hash(prompt)
    _purge_expired()
    row = con.execute("SELECT response, tokens, created_at FROM cache WHERE prompt_hash=?", (h,)).fetchone()
    if not row:
        return None
    response, tokens, created_at = row
    if datetime.now() - created_at > TTL:
        con.execute("DELETE FROM cache WHERE prompt_hash=?", (h,))
        return None
    return response, tokens


def put(prompt: str, response: str, tokens: int):
    _purge_expired()
    con.execute(
        "INSERT OR REPLACE INTO cache VALUES (?,?,?,?)",
        (_hash(prompt), response, tokens, datetime.now())
    )
