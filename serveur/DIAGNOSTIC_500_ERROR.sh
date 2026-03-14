#!/bin/bash
# Script de diagnostic pour l'erreur Internal Server Error

echo "🔍 Diagnostic complet de l'erreur Internal Server Error..."
echo ""

# 1. Statut de Gunicorn
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1. Statut de Gunicorn :"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
sudo systemctl status gunicorn.service --no-pager -l | head -20
echo ""

# 2. Logs Gunicorn récents
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "2. Logs Gunicorn récents (30 dernières lignes) :"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
sudo journalctl -u gunicorn.service -n 30 --no-pager | tail -30
echo ""

# 3. Logs Django
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "3. Logs Django (30 dernières lignes) :"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ -f "/home/ubuntu/IMS/backend/logs/django.log" ]; then
    tail -30 /home/ubuntu/IMS/backend/logs/django.log
else
    echo "⚠️  Fichier de log Django n'existe pas"
    echo "   Vérification du répertoire logs :"
    ls -la /home/ubuntu/IMS/backend/logs/ 2>/dev/null || echo "   Répertoire logs n'existe pas"
fi
echo ""

# 4. Vérification Django
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "4. Vérification Django (python manage.py check) :"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
cd /home/ubuntu/IMS/backend
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    python manage.py check 2>&1 | head -30
else
    echo "❌ Virtual environment non trouvé"
fi
echo ""

# 5. Variables d'environnement
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "5. Variables d'environnement critiques :"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ -f "/home/ubuntu/IMS/backend/.env" ]; then
    echo "✅ Fichier .env existe"
    echo ""
    echo "Variables présentes (valeurs masquées) :"
    grep -E "^(DEBUG|SECRET_KEY|ALLOWED_HOSTS|DATABASE)" /home/ubuntu/IMS/backend/.env | sed 's/=.*/=***/' || echo "⚠️  Variables non trouvées"
else
    echo "❌ Fichier .env n'existe pas"
    echo "   Créez-le à partir de env.example"
fi
echo ""

# 6. Test de connexion à la base de données
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "6. Test de connexion à la base de données :"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
cd /home/ubuntu/IMS/backend
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    python manage.py check --database default 2>&1 | head -15
else
    echo "❌ Virtual environment non trouvé"
fi
echo ""

# 7. Vérification des migrations
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "7. État des migrations :"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
cd /home/ubuntu/IMS/backend
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    python manage.py showmigrations --plan | head -20
else
    echo "❌ Virtual environment non trouvé"
fi
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Diagnostic terminé"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📋 Commandes utiles :"
echo "   - Voir les logs en temps réel : sudo journalctl -u gunicorn.service -f"
echo "   - Redémarrer Gunicorn : sudo systemctl restart gunicorn.service"
echo "   - Voir les erreurs détaillées : sudo journalctl -xeu gunicorn.service --no-pager | tail -50"

