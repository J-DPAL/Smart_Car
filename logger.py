import os, json, time
from datetime import datetime
from config import LOG_DIR

os.makedirs(LOG_DIR, exist_ok=True)

def log_jsonl(record: dict):
    # Write a single JSONL line into today's file with ISO timestamp
    ts = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    record['ts'] = ts
    filename = os.path.join(LOG_DIR, datetime.utcnow().strftime('%Y-%m-%d') + '.jsonl')
    with open(filename, 'a', encoding='utf-8') as f:
        f.write(json.dumps(record) + '\n')
