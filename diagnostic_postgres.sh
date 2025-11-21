#!/bin/bash

# Script de diagnostic PostgreSQL pour VPS
# Usage: ./diagnostic_postgres.sh

echo "=========================================="
echo "Diagnostic PostgreSQL - Connexion Docker"
echo "=========================================="
echo ""

# Couleurs pour la sortie
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. Vérifier si PostgreSQL est en cours d'exécution
echo "1. Vérification du service PostgreSQL..."
if systemctl is-active --quiet postgresql; then
    echo -e "${GREEN}✓ PostgreSQL est en cours d'exécution${NC}"
else
    echo -e "${RED}✗ PostgreSQL n'est pas en cours d'exécution${NC}"
    echo "   Commande pour démarrer: sudo systemctl start postgresql"
    exit 1
fi
echo ""

# 2. Trouver les fichiers de configuration
echo "2. Recherche des fichiers de configuration..."
POSTGRES_CONF=$(sudo find /etc/postgresql -name postgresql.conf 2>/dev/null | head -1)
PG_HBA=$(sudo find /etc/postgresql -name pg_hba.conf 2>/dev/null | head -1)

if [ -z "$POSTGRES_CONF" ]; then
    echo -e "${RED}✗ Fichier postgresql.conf introuvable${NC}"
    echo "   PostgreSQL pourrait être installé dans un autre emplacement"
else
    echo -e "${GREEN}✓ postgresql.conf trouvé: $POSTGRES_CONF${NC}"
fi

if [ -z "$PG_HBA" ]; then
    echo -e "${RED}✗ Fichier pg_hba.conf introuvable${NC}"
else
    echo -e "${GREEN}✓ pg_hba.conf trouvé: $PG_HBA${NC}"
fi
echo ""

# 3. Vérifier listen_addresses
echo "3. Vérification de listen_addresses..."
if [ -n "$POSTGRES_CONF" ]; then
    LISTEN_ADDR=$(sudo grep -E "^listen_addresses" "$POSTGRES_CONF" | grep -v "^#" | awk '{print $3}' | tr -d "'")
    if [ -z "$LISTEN_ADDR" ]; then
        echo -e "${YELLOW}⚠ listen_addresses n'est pas défini (par défaut: localhost)${NC}"
        echo "   Recommandation: Définir listen_addresses = '*'"
    elif [ "$LISTEN_ADDR" = "*" ]; then
        echo -e "${GREEN}✓ listen_addresses = '*' (correct)${NC}"
    else
        echo -e "${YELLOW}⚠ listen_addresses = $LISTEN_ADDR${NC}"
        echo "   Vérifiez que cette valeur inclut l'IP Docker (172.17.0.1)"
    fi
else
    echo -e "${YELLOW}⚠ Impossible de vérifier (fichier introuvable)${NC}"
fi
echo ""

# 4. Vérifier pg_hba.conf pour les connexions Docker
echo "4. Vérification de pg_hba.conf pour les connexions Docker..."
if [ -n "$PG_HBA" ]; then
    DOCKER_RULE=$(sudo grep -E "172\.17\.0\.0/16|172\.18\.0\.0/16|172\.19\.0\.0/16|172\.20\.0\.0/16" "$PG_HBA" | grep -v "^#")
    if [ -z "$DOCKER_RULE" ]; then
        echo -e "${RED}✗ Aucune règle pour le réseau Docker trouvée dans pg_hba.conf${NC}"
        echo "   Recommandation: Ajouter 'host all all 172.17.0.0/16 md5'"
    else
        echo -e "${GREEN}✓ Règle(s) Docker trouvée(s):${NC}"
        echo "$DOCKER_RULE" | while read line; do
            echo "   $line"
        done
    fi
else
    echo -e "${YELLOW}⚠ Impossible de vérifier (fichier introuvable)${NC}"
fi
echo ""

# 5. Vérifier que PostgreSQL écoute sur le port 5432
echo "5. Vérification du port d'écoute..."
LISTENING=$(sudo netstat -tlnp 2>/dev/null | grep ":5432 " || sudo ss -tlnp 2>/dev/null | grep ":5432 ")
if [ -z "$LISTENING" ]; then
    echo -e "${RED}✗ PostgreSQL n'écoute pas sur le port 5432${NC}"
else
    echo -e "${GREEN}✓ PostgreSQL écoute sur le port 5432:${NC}"
    echo "$LISTENING" | head -1
fi
echo ""

# 6. Vérifier l'utilisateur postgres
echo "6. Vérification de l'utilisateur PostgreSQL..."
USER_EXISTS=$(sudo -u postgres psql -tAc "SELECT 1 FROM pg_roles WHERE rolname='postgres'" 2>/dev/null)
if [ "$USER_EXISTS" = "1" ]; then
    echo -e "${GREEN}✓ L'utilisateur 'postgres' existe${NC}"
else
    echo -e "${RED}✗ L'utilisateur 'postgres' n'existe pas${NC}"
fi
echo ""

# 7. Vérifier la base de données inventairedb
echo "7. Vérification de la base de données 'inventairedb'..."
DB_EXISTS=$(sudo -u postgres psql -tAc "SELECT 1 FROM pg_database WHERE datname='inventairedb'" 2>/dev/null)
if [ "$DB_EXISTS" = "1" ]; then
    echo -e "${GREEN}✓ La base de données 'inventairedb' existe${NC}"
else
    echo -e "${YELLOW}⚠ La base de données 'inventairedb' n'existe pas${NC}"
    echo "   Commande pour créer: sudo -u postgres psql -c \"CREATE DATABASE inventairedb;\""
fi
echo ""

# 8. Tester la connexion avec le mot de passe
echo "8. Test de connexion (nécessite le mot de passe)..."
echo "   Exécutez manuellement:"
echo "   PGPASSWORD='Smatch2025' psql -h localhost -U postgres -d inventairedb -c 'SELECT version();'"
echo ""

# 9. Vérifier le firewall
echo "9. Vérification du firewall..."
if command -v ufw &> /dev/null; then
    UFW_STATUS=$(sudo ufw status | grep "5432/tcp")
    if [ -z "$UFW_STATUS" ]; then
        echo -e "${YELLOW}⚠ Le port 5432 n'est pas explicitement autorisé dans UFW${NC}"
        echo "   (Cela peut être normal si le firewall est désactivé ou si les règles sont différentes)"
    else
        echo -e "${GREEN}✓ Règle firewall trouvée:${NC}"
        echo "   $UFW_STATUS"
    fi
elif command -v firewall-cmd &> /dev/null; then
    FIREWALLD_STATUS=$(sudo firewall-cmd --list-ports 2>/dev/null | grep "5432")
    if [ -z "$FIREWALLD_STATUS" ]; then
        echo -e "${YELLOW}⚠ Le port 5432 n'est pas explicitement autorisé dans firewalld${NC}"
    else
        echo -e "${GREEN}✓ Port autorisé dans firewalld${NC}"
    fi
else
    echo -e "${YELLOW}⚠ Aucun gestionnaire de firewall détecté (ufw/firewalld)${NC}"
fi
echo ""

# 10. Trouver l'IP du bridge Docker
echo "10. Recherche de l'IP du bridge Docker..."
DOCKER_IP=$(ip addr show docker0 2>/dev/null | grep "inet " | awk '{print $2}' | cut -d/ -f1)
if [ -z "$DOCKER_IP" ]; then
    DOCKER_IP=$(docker network inspect bridge 2>/dev/null | grep -A 5 "IPAM" | grep "Gateway" | head -1 | awk '{print $2}' | tr -d '",')
fi

if [ -n "$DOCKER_IP" ]; then
    echo -e "${GREEN}✓ IP du bridge Docker: $DOCKER_IP${NC}"
    if [ "$DOCKER_IP" != "172.17.0.1" ]; then
        echo -e "${YELLOW}⚠ L'IP Docker ($DOCKER_IP) ne correspond pas à 172.17.0.1${NC}"
        echo "   Mettez à jour POSTGRES_HOST dans votre fichier .env"
    fi
else
    echo -e "${YELLOW}⚠ Impossible de déterminer l'IP du bridge Docker${NC}"
fi
echo ""

# Résumé et recommandations
echo "=========================================="
echo "Résumé et Actions Recommandées"
echo "=========================================="
echo ""
echo "Si des problèmes sont détectés, suivez ces étapes:"
echo ""
echo "1. Modifier postgresql.conf:"
echo "   sudo nano $POSTGRES_CONF"
echo "   Définir: listen_addresses = '*'"
echo ""
echo "2. Modifier pg_hba.conf:"
echo "   sudo nano $PG_HBA"
echo "   Ajouter à la fin: host all all 172.17.0.0/16 md5"
echo ""
echo "3. Redémarrer PostgreSQL:"
echo "   sudo systemctl restart postgresql"
echo ""
echo "4. Vérifier le mot de passe:"
echo "   sudo -u postgres psql -c \"ALTER USER postgres WITH PASSWORD 'Smatch2025';\""
echo ""
echo "5. Créer la base de données si nécessaire:"
echo "   sudo -u postgres psql -c \"CREATE DATABASE inventairedb;\""
echo ""
echo "6. Redémarrer le conteneur Docker:"
echo "   docker-compose restart web"
echo ""

