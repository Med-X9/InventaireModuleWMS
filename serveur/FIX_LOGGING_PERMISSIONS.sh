#!/bin/bash
# Script de correction des permissions pour les logs Django

echo "🔧 Correction des permissions pour les logs Django..."

# 1. Créer le répertoire de logs s'il n'existe pas
echo "📁 Création du répertoire de logs..."
sudo mkdir -p /home/ubuntu/IMS/backend/logs

# 2. Donner les permissions à www-data pour écrire dans les logs
echo "👤 Configuration des permissions pour www-data..."
sudo chown -R www-data:www-data /home/ubuntu/IMS/backend/logs
sudo chmod 755 /home/ubuntu/IMS/backend/logs

# 3. Tester que www-data peut écrire
echo "🧪 Test d'écriture avec www-data..."
if sudo -u www-data touch /home/ubuntu/IMS/backend/logs/test.log 2>/dev/null; then
    echo "✅ www-data peut écrire dans le répertoire de logs"
    sudo -u www-data rm /home/ubuntu/IMS/backend/logs/test.log
else
    echo "❌ www-data ne peut pas écrire dans le répertoire de logs"
    echo "   Vérification des permissions..."
    ls -ld /home/ubuntu/IMS/backend/logs
    exit 1
fi

echo ""
echo "✅ Permissions des logs corrigées avec succès !"
echo ""
echo "📋 Prochaines étapes :"
echo "   1. sudo systemctl restart gunicorn.service"
echo "   2. sudo systemctl status gunicorn.service"

