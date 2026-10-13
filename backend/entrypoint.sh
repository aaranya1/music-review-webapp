#!/bin/sh
set -e

# Apply pending migrations before serving. Safe for a single instance;
# with multiple replicas, run this as a separate one-off step instead.
flask --app app db upgrade

# Each worker is a separate process with its own in-memory rate-limit counts,
# so effective limits scale with WEB_CONCURRENCY unless RATELIMIT_STORAGE_URI
# points at a shared store such as Redis.
exec gunicorn app:app \
    --bind 0.0.0.0:8000 \
    --workers "${WEB_CONCURRENCY:-2}" \
    --timeout 60 \
    --access-logfile - \
    --error-logfile -
