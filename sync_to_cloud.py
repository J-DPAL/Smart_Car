# src/sync_to_cloud.py
import time, os, threading, json
import psycopg2
from urllib.parse import urlparse

def _connect(url):
    return psycopg2.connect(url, sslmode='require')

class CloudSync:
    def __init__(self, db_url, local_db: 'LocalDB', interval=30):
        self.db_url = db_url
        self.local_db = local_db
        self.interval = interval
        self._stop = threading.Event()
        self._t = threading.Thread(target=self._run, daemon=True)

    def start(self):
        if self.db_url:
            self._t.start()

    def stop(self):
        self._stop.set()
        self._t.join(timeout=2)

    def _ensure_table(self, conn):
        with conn.cursor() as cur:
            cur.execute("""
            CREATE TABLE IF NOT EXISTS telemetry (
                id SERIAL PRIMARY KEY,
                ts TIMESTAMP WITH TIME ZONE,
                mode TEXT,
                ir INTEGER,
                distance REAL,
                battery REAL,
                motor JSONB
            );""")
            conn.commit()

    def _run(self):
        while not self._stop.is_set():
            try:
                unsynced = self.local_db.get_unsynced(limit=200)
                if not unsynced:
                    time.sleep(self.interval)
                    continue
                conn = _connect(self.db_url)
                self._ensure_table(conn)
                ids = []
                with conn.cursor() as cur:
                    for r in unsynced:
                        ids.append(r['id'])
                        cur.execute("""
                            INSERT INTO telemetry (ts, mode, ir, distance, battery, motor)
                            VALUES (%s, %s, %s, %s, %s, %s)
                            """,
                            (r['ts'], r['mode'], r['ir'], r['distance'], r['battery'], json.dumps(r['motor']))
                        )
                    conn.commit()
                conn.close()
                # mark as synced locally
                self.local_db.mark_synced(ids)
            except Exception as e:
                print("[SYNC] error:", e)
            time.sleep(self.interval)
