#!/bin/sh
# Docker postgres ilk açılış: en az yetkili uygulama rolü (cth_app) + test veritabanı.
# Tablolar migration'larla owner ($POSTGRES_USER) tarafından oluşturulur; cth_app'e
# varsayılan yetkiler verilir. audit_logs üzerindeki UPDATE/DELETE yetkisi migration'da geri alınır.
set -eu
psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -v pw="$CTH_APP_DB_PASSWORD" <<'SQL'
CREATE ROLE cth_app LOGIN;
ALTER ROLE cth_app PASSWORD :'pw';
SQL
psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "CREATE DATABASE ${POSTGRES_DB}_test OWNER $POSTGRES_USER;"
for db in "$POSTGRES_DB" "${POSTGRES_DB}_test"; do
psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$db" <<SQL
GRANT CONNECT ON DATABASE $db TO cth_app;
GRANT USAGE ON SCHEMA public TO cth_app;
ALTER DEFAULT PRIVILEGES FOR ROLE $POSTGRES_USER IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO cth_app;
ALTER DEFAULT PRIVILEGES FOR ROLE $POSTGRES_USER IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO cth_app;
CREATE EXTENSION IF NOT EXISTS citext;
SQL
done
