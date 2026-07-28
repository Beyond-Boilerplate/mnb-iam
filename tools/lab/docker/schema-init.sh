#!/bin/sh
# Apply IIQ 8.5 PostgreSQL schema (same pattern as Helm schema-init job).
set -eu
echo "Waiting for Postgres…"
until pg_isready -h "$PGHOST" -p "$PGPORT" -U "$PGUSER"; do sleep 2; done

if psql -d postgres -Atc "SELECT 1 FROM pg_database WHERE datname='identityiq'" | grep -qx 1; then
  if psql -d identityiq -Atc "SELECT 1 FROM information_schema.tables WHERE table_schema='identityiq' AND table_name='spt_identity'" 2>/dev/null | grep -qx 1; then
    echo "IIQ schema already present — skipping"
    exit 0
  fi
fi

echo "Applying create_identityiq_tables-8.5.postgresql…"
sed \
  -e "s/ENCRYPTED PASSWORD 'identityiq'/ENCRYPTED PASSWORD '${IIQ_DB_PASSWORD}'/g" \
  -e "s/ENCRYPTED PASSWORD 'identityiqPlugin'/ENCRYPTED PASSWORD '${IIQ_PLUGIN_DB_PASSWORD}'/g" \
  -e "s/ENCRYPTED PASSWORD 'identityiqah'/ENCRYPTED PASSWORD '${IIQ_AH_DB_PASSWORD}'/g" \
  -e 's/\\connect identityiq identityiq/\\connect identityiq postgres\nSET ROLE identityiq;/' \
  -e 's/\\connect identityiqah identityiqah/\\connect identityiqah postgres\nSET ROLE identityiqah;/' \
  -e 's/\\connect "identityiqPlugin" "identityiqPlugin"/\\connect "identityiqPlugin" postgres\nSET ROLE "identityiqPlugin";/' \
  /sql/create_identityiq_tables-8.5.postgresql > /tmp/iiq-schema.sql

set +e
psql -v ON_ERROR_STOP=0 -d postgres -f /tmp/iiq-schema.sql > /tmp/schema.out 2>&1
rc=$?
set -e
tail -40 /tmp/schema.out || true

if ! psql -d identityiq -Atc "SELECT 1 FROM information_schema.tables WHERE table_schema='identityiq' AND table_name='spt_identity'" | grep -qx 1; then
  echo "ERROR: spt_identity missing after schema apply (psql rc=${rc})"
  exit 1
fi
echo "Schema init complete"
