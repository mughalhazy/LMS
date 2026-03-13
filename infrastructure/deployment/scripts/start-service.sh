#!/usr/bin/env sh
set -eu

if [ -n "${APP_MODULE:-}" ]; then
  exec python -m uvicorn "$APP_MODULE" --host 0.0.0.0 --port "${SERVICE_PORT:-8000}"
fi

if [ -n "${START_COMMAND:-}" ]; then
  exec sh -c "$START_COMMAND"
fi

echo "No APP_MODULE or START_COMMAND configured" >&2
exit 1
