#!/usr/bin/env bash
set -euo pipefail

DB_HOST="${POSTGRES_HOST:-db}"
DB_PORT="${POSTGRES_PORT:-5432}"
DB_NAME="${POSTGRES_DB:?POSTGRES_DB nao definido}"
DB_USER="${POSTGRES_USER:?POSTGRES_USER nao definido}"
DB_PASSWORD="${POSTGRES_PASSWORD:?POSTGRES_PASSWORD nao definido}"

export PGPASSWORD="${DB_PASSWORD}"

psql_base=(psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" -v ON_ERROR_STOP=1)

echo "Inicializando controle de migracoes..."
"${psql_base[@]}" <<'SQL'
CREATE TABLE IF NOT EXISTS schema_migrations (
    version VARCHAR(255) PRIMARY KEY,
    applied_at TIMESTAMP NOT NULL DEFAULT NOW()
);
SQL

echo "Aplicando migracoes SQL em ordem..."
for file in $(ls -1 /migrations/*.sql | sort); do
    version="$(basename "${file}")"
    already_applied="$("${psql_base[@]}" -tAc "SELECT 1 FROM schema_migrations WHERE version = '${version}' LIMIT 1;")"

    if [[ "${already_applied}" == "1" ]]; then
        echo " - Pulando ${version} (ja aplicada)"
        continue
    fi

    echo " - Aplicando ${version}"
    "${psql_base[@]}" -f "${file}"
    "${psql_base[@]}" -c "INSERT INTO schema_migrations (version) VALUES ('${version}');"
done

echo "Migracoes concluidas."
