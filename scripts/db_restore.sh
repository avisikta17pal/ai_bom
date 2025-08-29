#!/usr/bin/env bash
set -euo pipefail
DB_URL=${DATABASE_URL:-postgresql://postgres:postgres@localhost:5432/ai_bom}
IN=${1:?Usage: db_restore.sh <backup.sql>}
echo "Restoring ${IN} into ${DB_URL}"
psql "${DB_URL}" -f "${IN}"
echo "Done"

