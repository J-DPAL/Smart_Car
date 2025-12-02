# src/localdb.py
import sqlite3
import threading
import time
from datetime import datetime

SCHEMA = """
CREATE TABLE IF NOT EXISTS telemetry (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    mode TEXT,
    ir INTEGER,
    distance REAL,
    battery REAL,
    motor TEXT,
    synced INTEGER DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_telemetry_synced ON telemetry(synced);
"""

class LocalDB:
    def __init__(self, path):
        self.path = path
        self._lock = threading.Lock()
        self._init_db()

    def _conn(self):
        c = sqlite3.connect(self.path, timeout=30, check_same_thread=False)
        c.row_factory = sqlite3.Row
        return c

    def _init_db(self):
        with self._conn() as conn:
            conn.executescript(SCHEMA)

    def insert_telemetry(self, data):
        """
        data: dict with keys ts, mode, ir, distance, battery, motor
        """
        with self._lock:
            with self._conn() as conn:
                conn.execute(
                    "INSERT INTO telemetry (ts, mode, ir, distance, battery, motor, synced) VALUES (?, ?, ?, ?, ?, ?, 0)",
                    (data.get("ts"), data.get("mode"), data.get("ir"), data.get("distance"), data.get("battery"), str(data.get("motor")))
                )
                conn.commit()

    def get_unsynced(self, limit=200):
        with self._lock:
            with self._conn() as conn:
                rows = conn.execute("SELECT * FROM telemetry WHERE synced=0 ORDER BY id LIMIT ?", (limit,)).fetchall()
                return [dict(row) for row in rows]

    def mark_synced(self, ids):
        if not ids:
            return
        with self._lock:
            with self._conn() as conn:
                q = ",".join("?" for _ in ids)
                conn.execute(f"UPDATE telemetry SET synced=1 WHERE id IN ({q})", ids)
                conn.commit()
