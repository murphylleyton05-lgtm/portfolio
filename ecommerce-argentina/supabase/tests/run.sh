#!/usr/bin/env bash
# Aplica shim + migraciones + seed + tests sobre una base Postgres vacía.
# Uso: DATABASE_URL=postgres://postgres@localhost:5432/postgres ./supabase/tests/run.sh
set -euo pipefail

cd "$(dirname "$0")/.."
: "${DATABASE_URL:?Definí DATABASE_URL apuntando a un Postgres vacío}"

PSQL=(psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -q -X)

"${PSQL[@]}" -f tests/00_supabase_shim.sql
for migration in migrations/*.sql; do
  echo "→ $migration"
  "${PSQL[@]}" -f "$migration"
done
echo "→ seed.sql"
"${PSQL[@]}" -f seed.sql
for test in tests/[1-9]*.sql; do
  echo "→ $test"
  "${PSQL[@]}" -o /dev/null -f "$test"
done
echo "✓ Base de datos OK"
