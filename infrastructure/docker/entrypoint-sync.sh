#!/usr/bin/env bash
set -e

# Prefer POS_DB_* from env_file, then POSTGRES_*
DB_USER="$(echo -n "${POS_DB_USER:-${POSTGRES_USER:-postgres}}" | xargs)"
DB_PASS="${POS_DB_PASSWORD:-${POSTGRES_PASSWORD:-postgres}}"
DB_NAME="$(echo -n "${POS_DB_NAME:-${POSTGRES_DB:-$DB_USER}}" | xargs)"

export POSTGRES_USER="$DB_USER"
export POSTGRES_PASSWORD="$DB_PASS"
export POSTGRES_DB="$DB_NAME"

(
  until pg_isready -h 127.0.0.1 -p 5432 -q 2>/dev/null; do
    sleep 0.5
  done

  # Descubrir dinamicamente cualquier usuario administrativo existente
  ADMIN_USER=""
  CANDIDATES=("$DB_USER" "postgres")
  if [ -f /var/lib/postgresql/data/global/1260 ]; then
    while IFS= read -r role; do
      [ -n "$role" ] && CANDIDATES+=("$role")
    done < <(grep -aoE '[a-zA-Z0-9_]{3,30}' /var/lib/postgresql/data/global/1260 2>/dev/null | grep -Ev '^(pg_|SCRAM|SHA)' | head -n 5)
  fi

  for candidate in "${CANDIDATES[@]}"; do
    [ -z "$candidate" ] && continue
    if psql -h 127.0.0.1 -p 5432 -U "$candidate" -d postgres -tAc "SELECT 1" >/dev/null 2>&1; then
      ADMIN_USER="$candidate"
      break
    fi
  done

  if [ -n "$ADMIN_USER" ]; then
    # 1. Crear el usuario si no existe o actualizar su contrasena si ya existe
    psql -h 127.0.0.1 -p 5432 -U "$ADMIN_USER" -d postgres >/dev/null 2>&1 <<EOSQL
      DO \$\$
      BEGIN
        IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '$DB_USER') THEN
          CREATE ROLE "$DB_USER" WITH LOGIN SUPERUSER PASSWORD '$DB_PASS';
        ELSE
          ALTER ROLE "$DB_USER" WITH LOGIN SUPERUSER PASSWORD '$DB_PASS';
        END IF;
      END \$\$;
EOSQL

    # 2. Asegurar que 'postgres' tambien exista como superusuario para cualquier transicion futura
    psql -h 127.0.0.1 -p 5432 -U "$ADMIN_USER" -d postgres -c "
      DO \$\$
      BEGIN
        IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'postgres') THEN
          CREATE ROLE postgres WITH LOGIN SUPERUSER PASSWORD 'postgres';
        END IF;
      END \$\$;
    " >/dev/null 2>&1 || true

    # 3. Si venimos de mchange_me y se configuro otro nombre, renombrar para conservar datos
    if [ "$DB_NAME" != "mchange_me" ]; then
      psql -h 127.0.0.1 -p 5432 -U "$ADMIN_USER" -d postgres -c "ALTER DATABASE mchange_me RENAME TO \"$DB_NAME\";" >/dev/null 2>&1 || true
    fi

    # 4. Asegurar que la base de datos exista
    psql -h 127.0.0.1 -p 5432 -U "$ADMIN_USER" -d postgres >/dev/null 2>&1 <<EOSQL
      SELECT 'CREATE DATABASE "$DB_NAME" OWNER "$DB_USER"'
      WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '$DB_NAME')\gexec
EOSQL

    # 5. Asegurar permisos totales
    psql -h 127.0.0.1 -p 5432 -U "$ADMIN_USER" -d postgres -c "GRANT ALL PRIVILEGES ON DATABASE \"$DB_NAME\" TO \"$DB_USER\";" >/dev/null 2>&1 || true

    echo "[Docker POS-DB] Credenciales sincronizadas exitosamente: usuario '$DB_USER', base de datos '$DB_NAME'."
  fi
) &

exec docker-entrypoint.sh "$@"
