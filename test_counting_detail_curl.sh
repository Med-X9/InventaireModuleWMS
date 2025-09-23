#!/bin/bash

# Test de l'API CountingDetail avec cURL
# Remplacez TOKEN, COUNTING_ID, LOCATION_ID, PRODUCT_ID par vos valeurs

BASE_URL="http://localhost:8000"
API_BASE="$BASE_URL/mobile/api"

# Configuration
COUNTING_ID=1
LOCATION_ID=1
PRODUCT_ID=1
ASSIGNMENT_ID=1
TOKEN="YOUR_TOKEN_HERE"  # Remplacez par votre token d'authentification

echo "🧪 Test de l'API CountingDetail avec cURL"
echo "=========================================="

# 1. Test de création de CountingDetail (mode en vrac)
echo -e "\n1. Test de création de CountingDetail (mode en vrac)..."
curl -X POST \
  "$API_BASE/counting-detail/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"counting_id\": $COUNTING_ID,
    \"location_id\": $LOCATION_ID,
    \"quantity_inventoried\": 10,
    \"assignment_id\": $ASSIGNMENT_ID,
    \"dlc\": \"2024-12-31\",
    \"n_lot\": \"LOT123\"
  }" \
  -w "\nHTTP Status: %{http_code}\n"

# 2. Test de création de CountingDetail (mode par article)
echo -e "\n\n2. Test de création de CountingDetail (mode par article)..."
curl -X POST \
  "$API_BASE/counting-detail/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"counting_id\": $COUNTING_ID,
    \"location_id\": $LOCATION_ID,
    \"quantity_inventoried\": 5,
    \"assignment_id\": $ASSIGNMENT_ID,
    \"product_id\": $PRODUCT_ID,
    \"dlc\": \"2024-12-31\"
  }" \
  -w "\nHTTP Status: %{http_code}\n"

# 3. Test de création avec numéros de série
echo -e "\n\n3. Test de création avec numéros de série..."
curl -X POST \
  "$API_BASE/counting-detail/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"counting_id\": $COUNTING_ID,
    \"location_id\": $LOCATION_ID,
    \"quantity_inventoried\": 3,
    \"assignment_id\": $ASSIGNMENT_ID,
    \"product_id\": $PRODUCT_ID,
    \"numeros_serie\": [
      {\"n_serie\": \"NS001-2024\"},
      {\"n_serie\": \"NS002-2024\"},
      {\"n_serie\": \"NS003-2024\"}
    ]
  }" \
  -w "\nHTTP Status: %{http_code}\n"

# 4. Test de récupération des CountingDetail par comptage
echo -e "\n\n4. Test de récupération des CountingDetail par comptage..."
curl -X GET \
  "$API_BASE/counting-detail/?counting_id=$COUNTING_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -w "\nHTTP Status: %{http_code}\n"

# 5. Test de récupération par emplacement
echo -e "\n\n5. Test de récupération par emplacement..."
curl -X GET \
  "$API_BASE/counting-detail/?location_id=$LOCATION_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -w "\nHTTP Status: %{http_code}\n"

# 6. Test de récupération par produit
echo -e "\n\n6. Test de récupération par produit..."
curl -X GET \
  "$API_BASE/counting-detail/?product_id=$PRODUCT_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -w "\nHTTP Status: %{http_code}\n"

echo -e "\n\n🏁 Tests terminés!"
echo "Note: Assurez-vous d'avoir remplacé TOKEN, COUNTING_ID, LOCATION_ID, PRODUCT_ID par des valeurs valides"
echo "L'API respecte les règles de validation selon le mode de comptage:"
echo "- Mode 'en vrac': article non obligatoire"
echo "- Mode 'par article': article obligatoire"
echo "- Mode 'image de stock': article non obligatoire"
