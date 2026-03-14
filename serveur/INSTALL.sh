#!/bin/bash

# Script d'installation des fichiers de configuration serveur
# Usage: sudo bash serveur/INSTALL.sh

set -e  # Arrêter en cas d'erreur

echo "=========================================="
echo "Installation des fichiers de configuration"
echo "=========================================="

# Vérifier que le script est exécuté en root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Erreur: Ce script doit être exécuté avec sudo"
    echo "Usage: sudo bash serveur/INSTALL.sh"
    exit 1
fi

# Chemin du dossier serveur
SERVEUR_DIR="/home/ubuntu/IMS/backend/serveur"

# Vérifier que le dossier serveur existe
if [ ! -d "$SERVEUR_DIR" ]; then
    echo "❌ Erreur: Le dossier $SERVEUR_DIR n'existe pas"
    exit 1
fi

echo ""
echo "📁 1. Copie des fichiers systemd (Gunicorn)..."
echo "-------------------------------------------"

# Copier gunicorn.socket
if [ -f "$SERVEUR_DIR/gunicorn.socket" ]; then
    cp "$SERVEUR_DIR/gunicorn.socket" /etc/systemd/system/
    echo "✅ gunicorn.socket copié vers /etc/systemd/system/"
else
    echo "❌ Erreur: $SERVEUR_DIR/gunicorn.socket introuvable"
    exit 1
fi

# Copier gunicorn.service
if [ -f "$SERVEUR_DIR/gunicorn.service" ]; then
    cp "$SERVEUR_DIR/gunicorn.service" /etc/systemd/system/
    echo "✅ gunicorn.service copié vers /etc/systemd/system/"
else
    echo "❌ Erreur: $SERVEUR_DIR/gunicorn.service introuvable"
    exit 1
fi

echo ""
echo "📁 2. Copie de la configuration Nginx..."
echo "-------------------------------------------"

# Copier nginx-inventaire
if [ -f "$SERVEUR_DIR/nginx-inventaire" ]; then
    cp "$SERVEUR_DIR/nginx-inventaire" /etc/nginx/sites-available/inventaire
    echo "✅ nginx-inventaire copié vers /etc/nginx/sites-available/inventaire"
else
    echo "❌ Erreur: $SERVEUR_DIR/nginx-inventaire introuvable"
    exit 1
fi

# Créer le lien symbolique si il n'existe pas
if [ ! -L /etc/nginx/sites-enabled/inventaire ]; then
    ln -s /etc/nginx/sites-available/inventaire /etc/nginx/sites-enabled/
    echo "✅ Lien symbolique créé: /etc/nginx/sites-enabled/inventaire"
else
    echo "⚠️  Le lien symbolique existe déjà"
fi

# Supprimer la configuration par défaut si elle existe
if [ -L /etc/nginx/sites-enabled/default ]; then
    rm /etc/nginx/sites-enabled/default
    echo "✅ Configuration par défaut supprimée"
fi

echo ""
echo "🔄 3. Rechargement de systemd..."
echo "-------------------------------------------"
systemctl daemon-reload
echo "✅ systemd rechargé"

echo ""
echo "🚀 4. Activation et démarrage de Gunicorn..."
echo "-------------------------------------------"

# Activer le socket
systemctl enable gunicorn.socket
echo "✅ gunicorn.socket activé"

# Démarrer le socket
systemctl start gunicorn.socket
echo "✅ gunicorn.socket démarré"

# Vérifier le statut
echo ""
echo "📊 Statut de gunicorn.socket:"
systemctl status gunicorn.socket --no-pager -l || true

echo ""
echo "📊 Statut de gunicorn.service:"
systemctl status gunicorn.service --no-pager -l || true

echo ""
echo "✅ 5. Test de la configuration Nginx..."
echo "-------------------------------------------"
if nginx -t; then
    echo "✅ Configuration Nginx valide"
else
    echo "❌ Erreur dans la configuration Nginx"
    exit 1
fi

echo ""
echo "🔄 6. Rechargement de Nginx..."
echo "-------------------------------------------"
systemctl reload nginx
echo "✅ Nginx rechargé"

echo ""
echo "=========================================="
echo "✅ Installation terminée avec succès!"
echo "=========================================="
echo ""
echo "📋 Commandes utiles:"
echo "  - Voir les logs Gunicorn: sudo journalctl -u gunicorn.service -f"
echo "  - Voir les logs Nginx: sudo tail -f /var/log/nginx/inventaire-error.log"
echo "  - Redémarrer Gunicorn: sudo systemctl restart gunicorn.service"
echo "  - Redémarrer Nginx: sudo systemctl restart nginx"
echo "  - Vérifier le statut: sudo systemctl status gunicorn.service"
echo ""

