#!/bin/bash
# Script rapide de correction PostgreSQL - À exécuter sur le VPS
# Usage: sudo bash fix_postgres_quick.sh

POSTGRES_PASSWORD="Smatch2025"
POSTGRES_DB="inventairedb"

# Trouver les fichiers
POSTGRES_CONF=$(find /etc/postgresql -name postgresql.conf | head -1)
PG_HBA=$(find /etc/postgresql -name pg_hba.conf | head -1)

# 1. Modifier postgresql.conf
sed -i "s/#listen_addresses = 'localhost'/listen_addresses = '*'/" "$POSTGRES_CONF"
sed -i "s/^listen_addresses = 'localhost'/listen_addresses = '*'/" "$POSTGRES_CONF"
if ! grep -q "^listen_addresses" "$POSTGRES_CONF"; then
    echo "listen_addresses = '*'" >> "$POSTGRES_CONF"
fi

# 2. Modifier pg_hba.conf
if ! grep -qE "172\.(17|18|19|20)\.0\.0/16" "$PG_HBA"; then
    cat >> "$PG_HBA" <<EOF

# Autoriser les connexions depuis le réseau Docker
host    all             all             172.17.0.0/16          md5
host    all             all             172.18.0.0/16          md5
host    all             all             172.19.0.0/16          md5
host    all             all             172.20.0.0/16          md5
EOF
fi

# 3. Changer le mot de passe
sudo -u postgres psql <<EOF
ALTER USER postgres WITH PASSWORD '$POSTGRES_PASSWORD';
EOF

# 4. Créer la base de données si nécessaire
sudo -u postgres psql <<EOF
SELECT 1 FROM pg_database WHERE datname='$POSTGRES_DB' \gexec
\if :ERROR
CREATE DATABASE $POSTGRES_DB;
\endif
GRANT ALL PRIVILEGES ON DATABASE $POSTGRES_DB TO postgres;
EOF

# 5. Redémarrer PostgreSQL
systemctl restart postgresql

echo "✓ Configuration terminée!"
echo "Testez avec: PGPASSWORD=$POSTGRES_PASSWORD psql -h 172.17.0.1 -U postgres -d $POSTGRES_DB -c 'SELECT version();'"

