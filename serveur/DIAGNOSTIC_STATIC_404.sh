#!/bin/bash
# Script de diagnostic pour l'erreur 404 des fichiers statiques

echo "🔍 Diagnostic de l'erreur 404 pour les fichiers statiques..."
echo ""

# 1. Vérifier que le fichier existe
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1. Vérification de l'existence du fichier :"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
FILE_PATH="/home/ubuntu/IMS/backend/staticfiles/vendor/adminlte/js/adminlte.min.js"
if [ -f "$FILE_PATH" ]; then
    echo "✅ Fichier trouvé : $FILE_PATH"
    ls -lh "$FILE_PATH"
else
    echo "❌ Fichier NON trouvé : $FILE_PATH"
    echo ""
    echo "📁 Recherche de fichiers adminlte dans staticfiles :"
    find /home/ubuntu/IMS/backend/staticfiles -name "*adminlte*" -type f 2>/dev/null | head -10
    echo ""
    echo "📁 Vérification de la structure vendor :"
    ls -la /home/ubuntu/IMS/backend/staticfiles/vendor/ 2>/dev/null || echo "   Répertoire vendor n'existe pas"
fi
echo ""

# 2. Vérifier la configuration Nginx
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "2. Configuration Nginx pour /static/ :"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ -f "/etc/nginx/sites-available/inventaire" ]; then
    echo "Configuration dans /etc/nginx/sites-available/inventaire :"
    grep -A 5 "location /static/" /etc/nginx/sites-available/inventaire | head -6
elif [ -f "/etc/nginx/sites-enabled/inventaire" ]; then
    echo "Configuration dans /etc/nginx/sites-enabled/inventaire :"
    grep -A 5 "location /static/" /etc/nginx/sites-enabled/inventaire | head -6
else
    echo "⚠️  Fichier de configuration Nginx non trouvé"
    echo "   Fichiers disponibles :"
    ls -la /etc/nginx/sites-available/ 2>/dev/null
    ls -la /etc/nginx/sites-enabled/ 2>/dev/null
fi
echo ""

# 3. Vérifier que collectstatic a été exécuté
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "3. Vérification de collectstatic :"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ -d "/home/ubuntu/IMS/backend/staticfiles" ]; then
    FILE_COUNT=$(find /home/ubuntu/IMS/backend/staticfiles -type f | wc -l)
    echo "✅ Répertoire staticfiles existe"
    echo "   Nombre de fichiers : $FILE_COUNT"
    if [ "$FILE_COUNT" -eq 0 ]; then
        echo "   ⚠️  Aucun fichier dans staticfiles - collectstatic n'a probablement pas été exécuté"
    fi
else
    echo "❌ Répertoire staticfiles n'existe pas"
fi
echo ""

# 4. Vérifier les permissions
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "4. Permissions du répertoire staticfiles :"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
ls -ld /home/ubuntu/IMS/backend/staticfiles 2>/dev/null || echo "❌ Répertoire n'existe pas"
echo ""
echo "Test d'accès avec www-data :"
sudo -u www-data test -r /home/ubuntu/IMS/backend/staticfiles && echo "✅ www-data peut lire" || echo "❌ www-data ne peut pas lire"
echo ""

# 5. Vérifier les logs Nginx
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "5. Logs Nginx récents (erreurs static) :"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ -f "/var/log/nginx/inventaire-error.log" ]; then
    sudo tail -20 /var/log/nginx/inventaire-error.log | grep -i static || echo "   Aucune erreur static récente"
else
    echo "⚠️  Fichier de log d'erreur non trouvé"
fi
echo ""

# 6. Vérifier que jazzmin est installé
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "6. Vérification de django-jazzmin :"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
cd /home/ubuntu/IMS/backend
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    pip list | grep -i jazzmin && echo "✅ django-jazzmin installé" || echo "❌ django-jazzmin non installé"
else
    echo "⚠️  Virtual environment non trouvé"
fi
echo ""

# 7. Test de la configuration Nginx
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "7. Test de la configuration Nginx :"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
sudo nginx -t 2>&1
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Diagnostic terminé"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📋 Solutions possibles :"
echo "   1. Exécuter collectstatic : python manage.py collectstatic --noinput"
echo "   2. Vérifier que la config Nginx pointe vers staticfiles/ et non static/"
echo "   3. Recharger Nginx : sudo systemctl reload nginx"
echo "   4. Vérifier les permissions : sudo chmod -R 755 /home/ubuntu/IMS/backend/staticfiles"

