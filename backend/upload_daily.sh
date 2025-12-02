#!/usr/bin/env bash
# Simple uploader: uploads yesterday's log file to CLOUD_UPLOAD_URL using CLOUD_UPLOAD_TOKEN
# Export CLOUD_UPLOAD_URL and CLOUD_UPLOAD_TOKEN before running.
set -euo pipefail
DATE=$(date -d "yesterday" +%F)
FILE="logs/${DATE}.jsonl"

if [[ ! -f "$FILE" ]]; then
  echo "File $FILE not found."
  exit 1
fi

if [[ -z "${CLOUD_UPLOAD_URL:-}" ]]; then
  echo "CLOUD_UPLOAD_URL not set. Skipping upload."
  exit 2
fi

curl -X POST "$CLOUD_UPLOAD_URL" \
  -H "Authorization: Bearer ${CLOUD_UPLOAD_TOKEN:-}" \
  -F "file=@${FILE}"   || { echo "Upload failed"; exit 3; }

echo "Upload successful."
