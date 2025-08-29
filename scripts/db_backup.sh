#!/usr/bin/env bash
set -euo pipefail
DB_URL=${DATABASE_URL:-postgresql://postgres:postgres@localhost:5432/ai_bom}
OUT=${1:-backup_$(date +%Y%m%d_%H%M%S).sql}
echo "Backing up ${DB_URL} to ${OUT}"
pg_dump "${DB_URL}" > "${OUT}"
echo "Done"

