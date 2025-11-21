#!/bin/bash

# Script de correction automatique pour la connexion PostgreSQL
# Usage: sudo ./fix_postgres_connection.sh

set -e  # Arrêter en cas d'erreur

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=========================================="
echo "Correction de la Connexion PostgreSQL"
echo "==========================================${NC}"
echo ""

# Vérifier que le script est exécuté en tant que root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}✗ Ce script doit être exécuté avec sudo${NC}"
    echo "Usage: sudo ./fix_postgres_connection.sh"
    exit 1
fi

# Configuration
POSTGRES_PASSWORD="Smatch2025"
POSTGRES_DB="inventairedb"
POSTGRES_USER="postgres"

echo -e "${YELLOW}Configuration:${NC}"
echo "  Utilisateur: $POSTGRES_USER"
echo "  Base de données: $POSTGRES_DB"
echo "  Mot de passe: [masqué]"
echo ""

# 1. Trouver les fichiers de configuration
echo -e "${BLUE}[1/7] Recherche des fichiers de configuration...${NC}"
POSTGRES_CONF=$(find /etc/postgresql -name postgresql.conf 2>/dev/null | head -1)
PG_HBA=$(find /etc/postgresql -name pg_hba.conf 2>/dev/null | head -1)

if [ -z "$POSTGRES_CONF" ]; then
    echo -e "${RED}✗ Fichier postgresql.conf introuvable${NC}"
    echo "   Vérifiez que PostgreSQL est installé"
    exit 1
fi

if [ -z "$PG_HBA" ]; then
    echo -e "${RED}✗ Fichier pg_hba.conf introuvable${NC}"
    exit 1
fi

echo -e "${GREEN}✓ postgresql.conf: $POSTGRES_CONF${NC}"
echo -e "${GREEN}✓ pg_hba.conf: $PG_HBA${NC}"
echo ""

# 2. Sauvegarder les fichiers de configuration
echo -e "${BLUE}[2/7] Sauvegarde des fichiers de configuration...${NC}"
BACKUP_DIR="/tmp/postgres_backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
cp "$POSTGRES_CONF" "$BACKUP_DIR/postgresql.conf.backup"
cp "$PG_HBA" "$BACKUP_DIR/pg_hba.conf.backup"
echo -e "${GREEN}✓ Sauvegardes créées dans: $BACKUP_DIR${NC}"
echo ""

# 3. Modifier postgresql.conf pour écouter sur toutes les interfaces
echo -e "${BLUE}[3/7] Configuration de listen_addresses...${NC}"
if grep -q "^listen_addresses" "$POSTGRES_CONF"; then
    # Remplacer la ligne existante
    sed -i "s/^listen_addresses.*/listen_addresses = '*'/" "$POSTGRES_CONF"
    echo -e "${GREEN}✓ listen_addresses modifié${NC}"
else
    # Ajouter la ligne si elle n'existe pas
    echo "listen_addresses = '*'" >> "$POSTGRES_CONF"
    echo -e "${GREEN}✓ listen_addresses ajouté${NC}"
fi

# Commenter les lignes commentées qui pourraient interférer
sed -i "s/^#listen_addresses = 'localhost'/listen_addresses = '*'/" "$POSTGRES_CONF"
echo ""

# 4. Modifier pg_hba.conf pour autoriser les connexions Docker
echo -e "${BLUE}[4/7] Configuration de pg_hba.conf pour Docker...${NC}"

# Vérifier si la règle existe déjà
if grep -qE "172\.(17|18|19|20)\.0\.0/16" "$PG_HBA"; then
    echo -e "${YELLOW}⚠ Règle Docker déjà présente dans pg_hba.conf${NC}"
else
    # Ajouter les règles Docker avant la dernière ligne (généralement une ligne vide ou commentaire)
    # Ajouter à la fin du fichier
    {
        echo ""
        echo "# Autoriser les connexions depuis le réseau Docker"
        echo "host    all             all             172.17.0.0/16          md5"
        echo "host    all             all             172.18.0.0/16          md5"
        echo "host    all             all             172.19.0.0/16          md5"
        echo "host    all             all             172.20.0.0/16          md5"
    } >> "$PG_HBA"
    echo -e "${GREEN}✓ Règles Docker ajoutées à pg_hba.conf${NC}"
fi
echo ""

# 5. Changer le mot de passe PostgreSQL
echo -e "${BLUE}[5/7] Modification du mot de passe PostgreSQL...${NC}"
sudo -u postgres psql -c "ALTER USER $POSTGRES_USER WITH PASSWORD '$POSTGRES_PASSWORD';" 2>/dev/null || {
    echo -e "${YELLOW}⚠ Tentative de changement de mot de passe...${NC}"
    # Alternative: utiliser psql sans mot de passe en local
    sudo -u postgres psql <<EOF
ALTER USER $POSTGRES_USER WITH PASSWORD '$POSTGRES_PASSWORD';
\q
EOF
}
echo -e "${GREEN}✓ Mot de passe modifié${NC}"
echo ""

# 6. Créer la base de données si elle n'existe pas
echo -e "${BLUE}[6/7] Vérification/Création de la base de données...${NC}"
DB_EXISTS=$(sudo -u postgres psql -tAc "SELECT 1 FROM pg_database WHERE datname='$POSTGRES_DB'" 2>/dev/null || echo "0")
if [ "$DB_EXISTS" = "1" ]; then
    echo -e "${GREEN}✓ La base de données '$POSTGRES_DB' existe déjà${NC}"
else
    sudo -u postgres psql -c "CREATE DATABASE $POSTGRES_DB;" 2>/dev/null
    echo -e "${GREEN}✓ Base de données '$POSTGRES_DB' créée${NC}"
fi

# Donner les permissions
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $POSTGRES_DB TO $POSTGRES_USER;" 2>/dev/null || true
echo ""

# 7. Redémarrer PostgreSQL
echo -e "${BLUE}[7/7] Redémarrage de PostgreSQL...${NC}"
if systemctl is-active --quiet postgresql; then
    systemctl restart postgresql
    sleep 2
    if systemctl is-active --quiet postgresql; then
        echo -e "${GREEN}✓ PostgreSQL redémarré avec succès${NC}"
    else
        echo -e "${RED}✗ Erreur lors du redémarrage de PostgreSQL${NC}"
        echo "   Vérifiez les logs: sudo journalctl -u postgresql -n 50"
        exit 1
    fi
else
    echo -e "${YELLOW}⚠ PostgreSQL n'était pas en cours d'exécution, démarrage...${NC}"
    systemctl start postgresql
    sleep 2
fi
echo ""

# 8. Tests de vérification
echo -e "${BLUE}=========================================="
echo "Tests de Vérification"
echo "==========================================${NC}"
echo ""

# Test 1: Vérifier listen_addresses
echo -e "${BLUE}[Test 1] Vérification de listen_addresses...${NC}"
LISTEN_ADDR=$(sudo -u postgres psql -tAc "SHOW listen_addresses;" 2>/dev/null | xargs)
if [ "$LISTEN_ADDR" = "*" ]; then
    echo -e "${GREEN}✓ listen_addresses = * (correct)${NC}"
else
    echo -e "${YELLOW}⚠ listen_addresses = $LISTEN_ADDR${NC}"
fi
echo ""

# Test 2: Vérifier que PostgreSQL écoute sur le port 5432
echo -e "${BLUE}[Test 2] Vérification du port d'écoute...${NC}"
if netstat -tlnp 2>/dev/null | grep -q ":5432 " || ss -tlnp 2>/dev/null | grep -q ":5432 "; then
    echo -e "${GREEN}✓ PostgreSQL écoute sur le port 5432${NC}"
else
    echo -e "${RED}✗ PostgreSQL n'écoute pas sur le port 5432${NC}"
fi
echo ""

# Test 3: Tester la connexion avec le nouveau mot de passe
echo -e "${BLUE}[Test 3] Test de connexion avec le nouveau mot de passe...${NC}"
export PGPASSWORD="$POSTGRES_PASSWORD"
if psql -h localhost -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT version();" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Connexion réussie depuis localhost${NC}"
else
    echo -e "${RED}✗ Échec de la connexion depuis localhost${NC}"
    echo "   Vérifiez manuellement: psql -h localhost -U $POSTGRES_USER -d $POSTGRES_DB"
fi
unset PGPASSWORD
echo ""

# Test 4: Tester depuis l'IP Docker (172.17.0.1)
echo -e "${BLUE}[Test 4] Test de connexion depuis l'IP Docker (172.17.0.1)...${NC}"
export PGPASSWORD="$POSTGRES_PASSWORD"
if psql -h 172.17.0.1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT version();" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Connexion réussie depuis 172.17.0.1${NC}"
else
    echo -e "${YELLOW}⚠ Échec de la connexion depuis 172.17.0.1${NC}"
    echo "   Cela peut être normal si vous testez depuis le VPS lui-même"
    echo "   Le test depuis le conteneur Docker devrait fonctionner"
fi
unset PGPASSWORD
echo ""

# Résumé
echo -e "${BLUE}=========================================="
echo "Résumé"
echo "==========================================${NC}"
echo ""
echo -e "${GREEN}✓ Configuration terminée!${NC}"
echo ""
echo "Prochaines étapes:"
echo "1. Vérifiez que votre fichier .env contient:"
echo "   POSTGRES_HOST=172.17.0.1"
echo "   POSTGRES_USER=postgres"
echo "   POSTGRES_PASSWORD=Smatch2025"
echo "   POSTGRES_DB=inventairedb"
echo ""
echo "2. Redémarrez le conteneur Docker:"
echo "   docker-compose restart web"
echo ""
echo "3. Vérifiez les logs:"
echo "   docker logs inventaire-web --tail 50"
echo ""
echo -e "${YELLOW}Sauvegardes disponibles dans: $BACKUP_DIR${NC}"
echo ""

