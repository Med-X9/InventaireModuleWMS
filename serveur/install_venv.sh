#!/bin/bash

# Script d'installation de l'environnement virtuel Python
# Usage: bash serveur/install_venv.sh

set -e  # Arrêter en cas d'erreur

echo "=========================================="
echo "Installation de l'environnement virtuel"
echo "=========================================="

# Vérifier que python3 est installé
if ! command -v python3 &> /dev/null; then
    echo "❌ Erreur: python3 n'est pas installé"
    echo "Installez-le avec: sudo apt install python3 python3-pip python3-venv"
    exit 1
fi

# Chemin du projet
PROJECT_DIR="/home/ubuntu/IMS/backend"
VENV_DIR="$PROJECT_DIR/venv"

# Aller dans le dossier du projet
cd "$PROJECT_DIR" || exit 1

echo ""
echo "📦 1. Création de l'environnement virtuel..."
if [ -d "$VENV_DIR" ]; then
    echo "⚠️  Le venv existe déjà. Voulez-vous le recréer? (y/n)"
    read -r response
    if [ "$response" = "y" ]; then
        rm -rf "$VENV_DIR"
        python3 -m venv venv
        echo "✅ Venv recréé"
    else
        echo "✅ Utilisation du venv existant"
    fi
else
    python3 -m venv venv
    echo "✅ Venv créé"
fi

echo ""
echo "🔄 2. Activation du venv..."
source venv/bin/activate

echo ""
echo "📦 3. Mise à jour de pip..."
pip install --upgrade pip --quiet

echo ""
echo "📦 4. Installation des dépendances..."

if [ -f requirements.txt ]; then
    echo "   Installation depuis requirements.txt..."
    pip install -r requirements.txt
    echo "✅ Dépendances installées"
else
    echo "⚠️  requirements.txt non trouvé"
    echo "   Installation de gunicorn uniquement..."
    pip install gunicorn
    echo "✅ Gunicorn installé"
fi

echo ""
echo "✅ 5. Vérification de l'installation..."
GUNICORN_PATH=$(which gunicorn)
echo "   Chemin gunicorn: $GUNICORN_PATH"

if [ -n "$GUNICORN_PATH" ]; then
    GUNICORN_VERSION=$(gunicorn --version 2>&1 | head -n 1)
    echo "   Version: $GUNICORN_VERSION"
    echo "✅ Gunicorn installé correctement"
else
    echo "❌ Erreur: Gunicorn non trouvé"
    exit 1
fi

echo ""
echo "🔧 6. Configuration des permissions..."
sudo chmod -R 755 "$VENV_DIR"
echo "✅ Permissions configurées"

echo ""
echo "=========================================="
echo "✅ Installation terminée avec succès!"
echo "=========================================="
echo ""
echo "📝 Prochaines étapes:"
echo "  1. Copier gunicorn.service.venv vers /etc/systemd/system/gunicorn.service"
echo "     sudo cp $PROJECT_DIR/serveur/gunicorn.service.venv /etc/systemd/system/gunicorn.service"
echo ""
echo "  2. Recharger systemd"
echo "     sudo systemctl daemon-reload"
echo ""
echo "  3. Redémarrer le service"
echo "     sudo systemctl restart gunicorn.service"
echo ""
echo "  4. Vérifier le statut"
echo "     sudo systemctl status gunicorn.service"
echo ""

