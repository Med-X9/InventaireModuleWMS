#!/bin/bash

# Test de l'API Assignment sans body
# Remplacez TOKEN, USER_ID et ASSIGNMENT_ID par vos valeurs

BASE_URL="http://localhost:8000"
API_BASE="$BASE_URL/mobile/api"

# Configuration
USER_ID=1
ASSIGNMENT_ID=1
TOKEN="YOUR_TOKEN_HERE"  # Remplacez par votre token d'authentification

echo "🧪 Test de l'API Assignment (statut automatique ENTAME)"
echo "======================================================"

# Test de l'API assignment (sans body)
echo -e "\nTest de l'API assignment (statut automatique ENTAME)..."
curl -X POST \
  "$API_BASE/user/$USER_ID/assignment/$ASSIGNMENT_ID/status/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -w "\nHTTP Status: %{http_code}\n"

echo -e "\n\n🏁 Tests terminés!"
echo "Note: Assurez-vous d'avoir remplacé TOKEN, USER_ID et ASSIGNMENT_ID par des valeurs valides"
echo "L'API fonctionne maintenant SANS body - le statut ENTAME est appliqué automatiquement"
