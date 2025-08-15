#!/bin/bash

# Test de l'API des assignments avec cURL
# Remplacez les valeurs par vos données réelles

BASE_URL="http://localhost:8000"
API_BASE="$BASE_URL/api/mobile"

# Configuration
USER_ID=1
ASSIGNMENT_ID=1
TOKEN="YOUR_TOKEN_HERE"  # Remplacez par votre token d'authentification

echo "🧪 Test de l'API des assignments avec cURL"
echo "=========================================="

# Test de mise à jour des statuts
echo -e "\nMise à jour des statuts d'un assignment et de son job..."
curl -X POST \
  "$API_BASE/user/$USER_ID/assignment/$ASSIGNMENT_ID/status/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "new_status": "ENTAME"
  }' \
  -w "\nHTTP Status: %{http_code}\n"

echo -e "\n\n🏁 Tests terminés!"
echo "Note: Assurez-vous d'avoir remplacé TOKEN, USER_ID et ASSIGNMENT_ID par des valeurs valides"
