#!/bin/bash
# Script de diagnostic pour la connexion à la base de données

echo "🔍 Diagnostic de la connexion à la base de données..."
echo ""

# 1. Variables DATABASE dans .env
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1. Variables POSTGRES dans .env :"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ -f "/home/ubuntu/IMS/backend/.env" ]; then
    grep -E "^(POSTGRES_|DATABASE_)" /home/ubuntu/IMS/backend/.env | sed 's/PASSWORD=.*/PASSWORD=***/' || echo "⚠️  Variables POSTGRES non trouvées"
else
    echo "❌ Fichier .env n'existe pas"
fi
echo ""

# 2. Statut de PostgreSQL
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "2. Statut de PostgreSQL :"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
sudo systemctl status postgresql --no-pager | head -15 || echo "⚠️  PostgreSQL n'est pas installé ou ne fonctionne pas"
echo ""

# 3. Port PostgreSQL
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "3. Port PostgreSQL (5432) :"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
sudo ss -tlnp | grep 5432 || echo "⚠️  PostgreSQL n'écoute pas sur le port 5432"
echo ""

# 4. Test de connexion avec les variables du .env
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "4. Test de connexion PostgreSQL :"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ -f "/home/ubuntu/IMS/backend/.env" ]; then
    cd /home/ubuntu/IMS/backend
    source .env 2>/dev/null || true
    
    # Extraire les variables
    DB_NAME=$(grep "^POSTGRES_DB=" .env | cut -d'=' -f2)
    DB_USER=$(grep "^POSTGRES_USER=" .env | cut -d'=' -f2)
    DB_HOST=$(grep "^POSTGRES_HOST=" .env | cut -d'=' -f2)
    DB_PORT=$(grep "^POSTGRES_PORT=" .env | cut -d'=' -f2)
    
    echo "Tentative de connexion avec :"
    echo "  DB_NAME: $DB_NAME"
    echo "  DB_USER: $DB_USER"
    echo "  DB_HOST: $DB_HOST"
    echo "  DB_PORT: $DB_PORT"
    echo ""
    
    # Tester la connexion (sans mot de passe pour voir l'erreur)
    if command -v psql &> /dev/null; then
        echo "Test avec psql..."
        PGPASSWORD=$(grep "^POSTGRES_PASSWORD=" .env | cut -d'=' -f2) psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT version();" 2>&1 | head -5 || echo "❌ Échec de la connexion"
    else
        echo "⚠️  psql n'est pas installé"
    fi
else
    echo "❌ Fichier .env non trouvé"
fi
echo ""

# 5. Test de connexion Django
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "5. Test de connexion Django :"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
cd /home/ubuntu/IMS/backend
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    python manage.py check --database default 2>&1 | head -20
else
    echo "❌ Virtual environment non trouvé"
fi
echo ""

# 6. Vérifier si la base de données existe
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "6. Bases de données PostgreSQL existantes :"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if command -v psql &> /dev/null; then
    sudo -u postgres psql -l 2>/dev/null | head -10 || echo "⚠️  Impossible de lister les bases de données"
else
    echo "⚠️  psql n'est pas installé"
fi
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Diagnostic terminé"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📋 Solutions possibles :"
echo "   1. Vérifier que POSTGRES_PASSWORD dans .env correspond au mot de passe PostgreSQL"
echo "   2. Réinitialiser le mot de passe PostgreSQL : sudo -u postgres psql -c \"ALTER USER postgres WITH PASSWORD 'nouveau_mot_de_passe';\""
echo "   3. Créer la base de données si elle n'existe pas : sudo -u postgres createdb inventairedb"
echo "   4. Vérifier que PostgreSQL est en cours d'exécution : sudo systemctl start postgresql"

