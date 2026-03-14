#!/bin/bash
# Script pour corriger les fichiers statiques Django

echo "🔧 Correction des fichiers statiques Django..."
echo ""

# 1. Créer les répertoires s'ils n'existent pas
echo "📁 Création des répertoires..."
sudo mkdir -p /home/ubuntu/IMS/backend/staticfiles
sudo mkdir -p /home/ubuntu/IMS/backend/media

# 2. Collecter les fichiers statiques
echo "📦 Collecte des fichiers statiques..."
cd /home/ubuntu/IMS/backend
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    python manage.py collectstatic --noinput
    if [ $? -eq 0 ]; then
        echo "✅ Fichiers statiques collectés avec succès"
    else
        echo "❌ Erreur lors de la collecte des fichiers statiques"
        exit 1
    fi
else
    echo "❌ Virtual environment non trouvé"
    exit 1
fi

# 3. Ajuster les permissions
echo "🔐 Ajustement des permissions..."
sudo chown -R www-data:www-data /home/ubuntu/IMS/backend/staticfiles
sudo chown -R www-data:www-data /home/ubuntu/IMS/backend/media
sudo chmod -R 755 /home/ubuntu/IMS/backend/staticfiles
sudo chmod -R 755 /home/ubuntu/IMS/backend/media

# 4. Vérifier que Nginx peut lire
echo "🧪 Test d'accès Nginx..."
if sudo -u www-data test -r /home/ubuntu/IMS/backend/staticfiles; then
    echo "✅ Nginx peut lire le répertoire staticfiles"
else
    echo "❌ Nginx ne peut pas lire le répertoire staticfiles"
    exit 1
fi

# 5. Vérifier qu'il y a des fichiers
echo "📊 Vérification des fichiers..."
FILE_COUNT=$(find /home/ubuntu/IMS/backend/staticfiles -type f | wc -l)
if [ "$FILE_COUNT" -gt 0 ]; then
    echo "✅ $FILE_COUNT fichiers trouvés dans staticfiles"
else
    echo "⚠️  Aucun fichier dans staticfiles"
fi

# 6. Tester la configuration Nginx
echo "🔍 Test de la configuration Nginx..."
if sudo nginx -t 2>&1 | grep -q "successful"; then
    echo "✅ Configuration Nginx valide"
    echo "🔄 Rechargement de Nginx..."
    sudo systemctl reload nginx
    if [ $? -eq 0 ]; then
        echo "✅ Nginx rechargé avec succès"
    else
        echo "❌ Erreur lors du rechargement de Nginx"
        exit 1
    fi
else
    echo "❌ Erreur dans la configuration Nginx"
    sudo nginx -t
    exit 1
fi

echo ""
echo "✅ Fichiers statiques configurés avec succès !"
echo ""
echo "📋 Test :"
echo "   curl -I http://31.97.158.68/static/admin/css/base.css"
echo ""
echo "📋 Vérifier les logs :"
echo "   sudo tail -f /var/log/nginx/inventaire-error.log"

