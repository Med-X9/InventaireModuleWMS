#!/bin/bash
# Script pour mettre à jour la configuration Nginx avec la version corrigée

echo "🔄 Mise à jour de la configuration Nginx..."
echo ""

# 1. Sauvegarder l'ancienne configuration
echo "📦 Sauvegarde de l'ancienne configuration..."
sudo cp /etc/nginx/sites-available/inventaire /etc/nginx/sites-available/inventaire.backup.$(date +%Y%m%d_%H%M%S)
echo "✅ Sauvegarde créée"

# 2. Copier la nouvelle configuration
echo "📋 Copie de la nouvelle configuration..."
sudo cp /home/ubuntu/IMS/backend/serveur/nginx-inventaire /etc/nginx/sites-available/inventaire
if [ $? -eq 0 ]; then
    echo "✅ Configuration copiée"
else
    echo "❌ Erreur lors de la copie"
    exit 1
fi

# 3. Vérifier la syntaxe
echo "🔍 Vérification de la syntaxe..."
if sudo nginx -t 2>&1 | grep -q "successful"; then
    echo "✅ Syntaxe Nginx valide"
else
    echo "❌ Erreur de syntaxe dans la configuration"
    sudo nginx -t
    echo ""
    echo "🔄 Restauration de la sauvegarde..."
    sudo cp /etc/nginx/sites-available/inventaire.backup.* /etc/nginx/sites-available/inventaire
    exit 1
fi

# 4. Vérifier que la regex a l'exclusion
echo "🔍 Vérification de la regex frontend..."
if grep -q "(?!static|media)" /etc/nginx/sites-available/inventaire; then
    echo "✅ Regex frontend a l'exclusion (?!static|media)"
else
    echo "⚠️  Regex frontend n'a pas l'exclusion - vérification manuelle nécessaire"
fi

# 5. Vérifier que try_files est présent
echo "🔍 Vérification de try_files dans /static/..."
if grep -A 5 "location /static/" /etc/nginx/sites-available/inventaire | grep -q "try_files"; then
    echo "✅ try_files présent dans location /static/"
else
    echo "⚠️  try_files manquant dans location /static/"
fi

# 6. Recharger Nginx
echo "🔄 Rechargement de Nginx..."
sudo systemctl reload nginx
if [ $? -eq 0 ]; then
    echo "✅ Nginx rechargé avec succès"
else
    echo "❌ Erreur lors du rechargement de Nginx"
    exit 1
fi

echo ""
echo "✅ Configuration mise à jour !"
echo ""
echo "📋 Test :"
echo "   curl -I http://31.97.158.68/static/vendor/adminlte/js/adminlte.min.js"
echo ""
echo "📋 Vérification de la configuration :"
echo "   sudo grep -A 5 'location /static/' /etc/nginx/sites-available/inventaire"
echo "   sudo grep -A 3 'location ~\*' /etc/nginx/sites-available/inventaire | grep static"

