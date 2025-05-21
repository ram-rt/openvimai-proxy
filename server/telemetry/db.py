import duckdb, json
from datetime import datetime
from core.settings import settings

tcon = duckdb.connect(settings.telemetry_db, read_only=False)
tcon.execute("""
CREATE TABLE IF NOT EXISTS telemetry (
    ts TIMESTAMP,
    event_type VARCHAR,
    payload JSON
)
""")

def record(event_type: str, payload: dict, ts: datetime | None = None):
    if ts is None:
        ts = datetime.now()
    tcon.execute("INSERT INTO telemetry VALUES (?,?,?)",
                 (ts, event_type, json.dumps(payload)))