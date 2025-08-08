#!/bin/bash

# Script de test pour l'API des stocks avec curl
# Teste l'API pour récupérer les stocks du même compte qu'un utilisateur

echo "=== Test de l'API des stocks avec curl ==="

# Configuration
BASE_URL="http://localhost:8000"
USER_ID=3
API_URL="${BASE_URL}/api/mobile/user/${USER_ID}/stocks/"

echo "URL: ${API_URL}"
echo "User ID: ${USER_ID}"
echo ""

# Test de l'API
echo "🔍 Test de récupération des stocks..."
echo "curl -X GET ${API_URL}"
echo ""

response=$(curl -s -w "\n%{http_code}" -X GET "${API_URL}")

# Extraire le body et le status code
body=$(echo "$response" | head -n -1)
status_code=$(echo "$response" | tail -n 1)

echo "📊 Status Code: ${status_code}"
echo ""

if [ "$status_code" -eq 200 ]; then
    echo "✅ Réponse réussie:"
    echo "$body" | python3 -m json.tool 2>/dev/null || echo "$body"
    
    # Analyser la réponse
    success=$(echo "$body" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('success', False))" 2>/dev/null)
    
    if [ "$success" = "True" ]; then
        stocks_count=$(echo "$body" | python3 -c "import sys, json; data=json.load(sys.stdin); print(len(data.get('data', {}).get('stocks', [])))" 2>/dev/null)
        echo ""
        echo "📊 Nombre de stocks trouvés: ${stocks_count}"
        
        if [ "$stocks_count" -gt 0 ]; then
            echo ""
            echo "📋 Aperçu des stocks:"
            echo "$body" | python3 -c "
import sys, json
data = json.load(sys.stdin)
stocks = data.get('data', {}).get('stocks', [])
for i, stock in enumerate(stocks[:3], 1):
    print(f'  Stock {i}:')
    print(f'    - ID: {stock.get(\"web_id\")}')
    print(f'    - Référence: {stock.get(\"reference\")}')
    print(f'    - Location: {stock.get(\"location_reference\")}')
    print(f'    - Produit: {stock.get(\"product_name\")}')
    print(f'    - Quantité disponible: {stock.get(\"quantity_available\")}')
    print(f'    - Unité: {stock.get(\"unit_name\")}')
    print()
if len(stocks) > 3:
    print(f'  ... et {len(stocks) - 3} autres stocks')
" 2>/dev/null
        else
            echo "ℹ️  Aucun stock trouvé pour cet utilisateur"
        fi
    else
        echo "❌ Erreur dans la réponse:"
        error_msg=$(echo "$body" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('error', 'Erreur inconnue'))" 2>/dev/null)
        error_type=$(echo "$body" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('error_type', 'Erreur inconnue'))" 2>/dev/null)
        echo "   - Message: ${error_msg}"
        echo "   - Type: ${error_type}"
    fi
else
    echo "❌ Erreur HTTP:"
    echo "   - Status: ${status_code}"
    echo "   - Contenu: ${body}"
fi

echo ""
echo "=== Fin du test ===" 