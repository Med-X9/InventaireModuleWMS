#!/bin/bash

# Script pour configurer gunicorn.service avec venv
# Usage: sudo bash serveur/SETUP_GUNICORN_VENV.sh

set -e

echo "=========================================="
echo "Configuration de gunicorn.service avec venv"
echo "=========================================="

# Vérifier que le script est exécuté en root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Erreur: Ce script doit être exécuté avec sudo"
    echo "Usage: sudo bash serveur/SETUP_GUNICORN_VENV.sh"
    exit 1
fi

VENV_PATH="/home/ubuntu/IMS/backend/venv"
GUNICORN_PATH="$VENV_PATH/bin/gunicorn"

# Vérifier que le venv existe
if [ ! -f "$GUNICORN_PATH" ]; then
    echo "❌ Erreur: Gunicorn non trouvé dans $GUNICORN_PATH"
    echo "Assurez-vous que le venv est installé et que gunicorn est installé"
    exit 1
fi

echo ""
echo "✅ Gunicorn trouvé: $GUNICORN_PATH"

# Créer le fichier gunicorn.service
cat > /etc/systemd/system/gunicorn.service << 'EOF'
[Unit]
Description=gunicorn daemon
Requires=gunicorn.socket
After=network.target

[Service]
Type=notify

# Nom d'utilisateur et groupe qui exécutent le processus
User=www-data
Group=www-data

# Répertoire de travail (chemin vers votre projet Django)
WorkingDirectory=/home/ubuntu/IMS/backend

# Environnement virtuel Python
Environment="PATH=/home/ubuntu/IMS/backend/venv/bin"
ExecStart=/home/ubuntu/IMS/backend/venv/bin/gunicorn \
          --access-logfile - \
          --workers 3 \
          --threads 2 \
          --timeout 600 \
          --bind unix:/run/gunicorn.sock \
          project.wsgi:application

# Redémarrer automatiquement en cas d'échec
Restart=on-failure

# Sécurité : empêcher l'accès aux fichiers système
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF

echo "✅ Fichier gunicorn.service créé dans /etc/systemd/system/"

echo ""
echo "🔄 Rechargement de systemd..."
systemctl daemon-reload
echo "✅ systemd rechargé"

echo ""
echo "🚀 Activation et démarrage du service..."
systemctl enable gunicorn.service
systemctl restart gunicorn.service

echo ""
echo "📊 Statut du service:"
systemctl status gunicorn.service --no-pager -l || true

echo ""
echo "=========================================="
echo "✅ Configuration terminée!"
echo "=========================================="
echo ""
echo "Commandes utiles:"
echo "  - Voir les logs: sudo journalctl -u gunicorn.service -f"
echo "  - Redémarrer: sudo systemctl restart gunicorn.service"
echo "  - Statut: sudo systemctl status gunicorn.service"
echo ""

