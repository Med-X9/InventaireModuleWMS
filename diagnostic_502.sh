#!/bin/bash
# Script de diagnostic pour le problème 502 Bad Gateway
# Usage: ./diagnostic_502.sh

echo "=========================================="
echo "Diagnostic 502 Bad Gateway"
echo "=========================================="
echo ""

echo "1. Vérification des conteneurs..."
docker ps | grep -E "inventaire-nginx|inventaire-web"
echo ""

echo "2. Logs récents de nginx (dernières 20 lignes)..."
docker logs inventaire-nginx --tail 20
echo ""

echo "3. Logs récents du backend (dernières 20 lignes)..."
docker logs inventaire-web --tail 20
echo ""

echo "4. Vérification du réseau..."
docker network inspect inventaire-net 2>/dev/null | grep -A 5 "Containers" || echo "⚠️  Le réseau inventaire-net n'existe pas ou n'est pas accessible"
echo ""

echo "5. Test de connectivité depuis nginx vers le backend..."
if docker exec inventaire-nginx ping -c 2 web > /dev/null 2>&1; then
    echo "✅ Ping réussi: nginx peut joindre le backend"
else
    echo "❌ Ping échoué: problème de réseau ou de résolution DNS"
fi
echo ""

echo "6. Test de connexion HTTP depuis nginx..."
if docker exec inventaire-nginx curl -s -o /dev/null -w "%{http_code}" http://web:8000/admin/ 2>/dev/null | grep -q "200\|301\|302\|403"; then
    echo "✅ Connexion HTTP réussie"
else
    echo "❌ Connexion HTTP échouée - c'est probablement la cause du 502"
    echo "   Détails de l'erreur:"
    docker exec inventaire-nginx curl -v http://web:8000/admin/ 2>&1 | tail -10
fi
echo ""

echo "7. Vérification que le backend écoute sur le port 8000..."
if docker exec inventaire-web netstat -tlnp 2>/dev/null | grep -q ":8000" || docker exec inventaire-web ss -tlnp 2>/dev/null | grep -q ":8000"; then
    echo "✅ Le backend écoute sur le port 8000"
else
    echo "❌ Le backend n'écoute pas sur le port 8000"
    echo "   Processus en cours:"
    docker exec inventaire-web ps aux | head -10
fi
echo ""

echo "8. Vérification des processus Gunicorn..."
if docker exec inventaire-web ps aux | grep -q gunicorn; then
    echo "✅ Gunicorn est en cours d'exécution"
    docker exec inventaire-web ps aux | grep gunicorn
else
    echo "❌ Gunicorn n'est pas en cours d'exécution"
fi
echo ""

echo "9. Test direct depuis l'hôte vers le backend..."
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/admin/ 2>/dev/null | grep -q "200\|301\|302\|403"; then
    echo "✅ Le backend répond directement sur le port 8000"
else
    echo "❌ Le backend ne répond pas sur le port 8000"
fi
echo ""

echo "=========================================="
echo "Résumé et recommandations"
echo "=========================================="
echo ""
echo "Si le problème persiste, essayez:"
echo "1. docker restart inventaire-web"
echo "2. Attendre 10 secondes"
echo "3. docker restart inventaire-nginx"
echo "4. Vérifier les logs: docker logs -f inventaire-web"
echo ""

