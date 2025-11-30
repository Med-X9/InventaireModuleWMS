#!/bin/bash
# Script de correction des permissions pour Gunicorn

echo "🔧 Correction des permissions pour Gunicorn..."

# 1. Vérifier/créer les répertoires
echo "📁 Vérification des répertoires..."
sudo mkdir -p /home/ubuntu/IMS/backend
sudo mkdir -p /home/ubuntu/IMS/backend/venv

# 2. Corriger les permissions des répertoires parents (nécessaire pour traverser le chemin)
echo "🔐 Correction des permissions des répertoires parents..."
sudo chmod 755 /home
sudo chmod 755 /home/ubuntu
sudo chmod 755 /home/ubuntu/IMS

# 3. Ajuster les permissions du répertoire backend (ubuntu propriétaire)
echo "📂 Correction des permissions du répertoire backend..."
sudo chown -R ubuntu:ubuntu /home/ubuntu/IMS/backend

# 4. Permettre à www-data de lire/exécuter dans le répertoire backend
echo "👤 Configuration des permissions pour www-data..."
sudo chmod 755 /home/ubuntu/IMS/backend

# 5. Permissions pour le venv (lecture/exécution pour www-data)
echo "🐍 Configuration des permissions du venv..."
if [ -d "/home/ubuntu/IMS/backend/venv" ]; then
    sudo chmod -R 755 /home/ubuntu/IMS/backend/venv
    sudo chmod 755 /home/ubuntu/IMS/backend/venv/bin
    if [ -f "/home/ubuntu/IMS/backend/venv/bin/gunicorn" ]; then
        sudo chmod 755 /home/ubuntu/IMS/backend/venv/bin/gunicorn
    fi
fi

# 6. Tester l'accès avec www-data
echo "🧪 Test d'accès avec www-data..."
if sudo -u www-data test -r /home/ubuntu/IMS/backend; then
    echo "✅ www-data peut lire le répertoire backend"
else
    echo "❌ www-data ne peut pas lire le répertoire backend"
    exit 1
fi

if sudo -u www-data test -x /home/ubuntu/IMS/backend; then
    echo "✅ www-data peut exécuter dans le répertoire backend"
else
    echo "❌ www-data ne peut pas exécuter dans le répertoire backend"
    exit 1
fi

# 7. Tester gunicorn
echo "🚀 Test de gunicorn..."
if [ -f "/home/ubuntu/IMS/backend/venv/bin/gunicorn" ]; then
    if sudo -u www-data /home/ubuntu/IMS/backend/venv/bin/gunicorn --version > /dev/null 2>&1; then
        echo "✅ gunicorn est exécutable par www-data"
        sudo -u www-data /home/ubuntu/IMS/backend/venv/bin/gunicorn --version
    else
        echo "❌ gunicorn n'est pas exécutable par www-data"
        exit 1
    fi
else
    echo "⚠️  gunicorn n'existe pas dans le venv"
fi

echo ""
echo "✅ Permissions corrigées avec succès !"
echo ""
echo "📋 Prochaines étapes :"
echo "   1. sudo systemctl daemon-reload"
echo "   2. sudo systemctl restart gunicorn.service"
echo "   3. sudo systemctl status gunicorn.service"

