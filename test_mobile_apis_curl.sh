#!/bin/bash

# Script de test pour les APIs Mobile avec curl
# Usage: ./test_mobile_apis_curl.sh

BASE_URL="http://localhost:8000"
API_BASE="$BASE_URL/api/mobile"

echo "🚀 Test des APIs Mobile avec curl"
echo "📍 URL de base: $BASE_URL"
echo "📡 API Mobile: $API_BASE"
echo ""

# Test 1: Login
echo "🔐 Test de connexion..."
LOGIN_RESPONSE=$(curl -s -X POST "$API_BASE/auth/login/" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123"
  }')

echo "Response:"
echo "$LOGIN_RESPONSE" | jq '.' 2>/dev/null || echo "$LOGIN_RESPONSE"
echo ""

# Extraire le token
TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.access' 2>/dev/null)

if [ "$TOKEN" != "null" ] && [ "$TOKEN" != "" ]; then
    echo "✅ Login réussi! Token extrait."
    echo ""
    
    # Test 2: Synchronisation des données
    echo "📥 Test de synchronisation des données..."
    SYNC_RESPONSE=$(curl -s -X GET "$API_BASE/sync/data/" \
      -H "Content-Type: application/json" \
      -H "Authorization: Bearer $TOKEN")
    
    echo "Response:"
    echo "$SYNC_RESPONSE" | jq '.' 2>/dev/null || echo "$SYNC_RESPONSE"
    echo ""
    
    # Test 3: Upload des données
    echo "📤 Test d'upload des données..."
    UPLOAD_RESPONSE=$(curl -s -X POST "$API_BASE/sync/upload/" \
      -H "Content-Type: application/json" \
      -H "Authorization: Bearer $TOKEN" \
      -d '{
        "sync_id": "test_sync_123456789",
        "countings": [
          {
            "detail_id": "detail_123456789",
            "quantite_comptee": 25,
            "product_web_id": 1,
            "location_web_id": 1,
            "numero_lot": "LOT-TEST-2024",
            "numero_serie": null,
            "dlc": "2024-12-31",
            "compte_par_web_id": 1,
            "date_comptage": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'"
          }
        ],
        "assignments": [
          {
            "assignment_web_id": 1,
            "status": "ENTAME",
            "entame_date": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'",
            "date_start": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'"
          }
        ]
      }')
    
    echo "Response:"
    echo "$UPLOAD_RESPONSE" | jq '.' 2>/dev/null || echo "$UPLOAD_RESPONSE"
    echo ""
    
    # Test 4: Logout
    echo "🚪 Test de déconnexion..."
    LOGOUT_RESPONSE=$(curl -s -X POST "$API_BASE/auth/logout/" \
      -H "Content-Type: application/json" \
      -H "Authorization: Bearer $TOKEN")
    
    echo "Response:"
    echo "$LOGOUT_RESPONSE" | jq '.' 2>/dev/null || echo "$LOGOUT_RESPONSE"
    echo ""
    
    echo "🎉 Tests terminés!"
else
    echo "❌ Échec de l'authentification. Arrêt des tests."
fi 